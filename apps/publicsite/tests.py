from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.publicsite.models import PublicContentPage


class PublicWebsiteSmokeTests(TestCase):
    def setUp(self):
        for slug, title in (
            ('privacy-policy', 'Privacy Policy'),
            ('terms-conditions', 'Terms & Conditions'),
            ('refund-policy', 'Refund Policy'),
            ('disclaimer', 'Disclaimer'),
        ):
            PublicContentPage.objects.get_or_create(
                page_type=slug,
                defaults={'title': title, 'content': 'Public information.', 'is_published': True},
            )

    def test_primary_public_routes_load(self):
        names = (
            'home', 'about', 'blog-list', 'news-list', 'contact', 'faq',
            'event-list', 'partners', 'sponsors', 'careers', 'team-list',
            'gallery', 'live-scores', 'match-center',
        )
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f'publicsite:{name}')).status_code, 200)

    def test_policy_routes_load(self):
        for slug in ('privacy-policy', 'terms-conditions', 'refund-policy', 'disclaimer'):
            response = self.client.get(reverse('publicsite:public-content', kwargs={'page_type': slug}))
            self.assertEqual(response.status_code, 200)

    def test_seo_endpoints_and_metadata(self):
        self.assertEqual(self.client.get(reverse('publicsite:robots')).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:sitemap')).status_code, 200)
        response = self.client.get(reverse('publicsite:home'))
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'property="og:title"')

    def test_filters_do_not_break(self):
        self.assertEqual(self.client.get(reverse('publicsite:match-center'), {'status': 'live'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:event-list'), {'search': 'Mumbai'}).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:team-list'), {'search': 'RNT'}).status_code, 200)

    def test_dedicated_cms_requires_login(self):
        response = self.client.get('/website-admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/website-admin/login/', response.url)

    def test_dedicated_cms_only_lists_publicsite_models(self):
        user = get_user_model().objects.create_superuser(
            email='cms@example.com', password='StrongPass123!'
        )
        self.client.force_login(user)
        response = self.client.get('/website-admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Website Content Manager')
        self.assertNotContains(response, 'Tournament Matches')

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_custom_404(self):
        response = self.client.get('/page-that-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page Not Found', status_code=404)



class PlayerOnboardingFlowTests(TestCase):
    def test_guest_and_choice_pages_load(self):
        self.assertEqual(self.client.get(reverse('publicsite:guest-welcome')).status_code, 200)
        self.assertEqual(self.client.get(reverse('publicsite:registration-choice')).status_code, 200)

    def test_direct_register_requires_account_type_choice(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertRedirects(response, reverse('publicsite:registration-choice'))
        response = self.client.get(reverse('accounts:register') + '?type=general')
        self.assertEqual(response.status_code, 200)

    def test_player_journey_persists_across_steps(self):
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 1}), {
            'full_name': 'Test Player', 'date_of_birth': '2000-01-01',
            'gender': 'MALE', 'phone': '9876543210', 'city': 'Mumbai', 'state': 'Maharashtra',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey', kwargs={'step': 2}))
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 2}), {
            'role': 'BATTER', 'batting_style': 'RIGHT_HAND', 'bowling_style': '',
            'jersey_number': '18', 'height_cm': '178', 'weight_kg': '72',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey', kwargs={'step': 3}))
        response = self.client.post(reverse('publicsite:player-journey', kwargs={'step': 3}), {
            'playing_experience': '5', 'academy_or_club': 'Test Academy',
            'highest_level': 'ACADEMY', 'achievements': 'Top scorer',
            'emergency_contact_name': 'Parent', 'emergency_contact_phone': '9876500000',
            'consent_accepted': 'on',
        })
        self.assertRedirects(response, reverse('publicsite:player-journey-review'))
        self.assertEqual(self.client.session['player_journey']['role'], 'BATTER')

    def test_review_moves_player_to_account_creation(self):
        session = self.client.session
        session['player_journey'] = {'full_name': 'Test Player', 'phone': '9876543210'}
        session.save()
        response = self.client.post(reverse('publicsite:player-journey-review'))
        self.assertRedirects(response, reverse('accounts:register'))
        self.assertEqual(self.client.session['registration_type'], 'PLAYER')
