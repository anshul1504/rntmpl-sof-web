from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.publicsite.models import (
    AboutPageSettings,
    BlogSettings,
    CareerPageSettings,
    ContactPageSettings,
    EventPageSettings,
    GalleryItem,
    GalleryPageSettings,
    HeroSlide,
    HomePage,
    NewsPost,
    NewsPageSettings,
    PartnerPageSettings,
    FAQPageSettings,
    SponsorPageSettings,
    TeamPageSettings,
    WebsiteFeature,
    WebsiteSettings,
)


class Command(BaseCommand):
    help = 'Seed the public website CMS with RNTMPL demo content and reference assets.'

    @staticmethod
    def _assign_file(instance, field_name, file_path, save=True):
        if not file_path.exists():
            return False
        with file_path.open('rb') as file_handle:
            getattr(instance, field_name).save(file_path.name, File(file_handle), save=save)
        return True

    def handle(self, *args, **options):
        site, _ = WebsiteSettings.objects.get_or_create(pk=1)
        site.site_name = 'RNTMPL'
        site.tagline = 'Bharat Ka Cricket, Har Player Ka Sapna'
        site.announcement = 'Player Registrations Are Now Open'
        site.contact_phone = '+91 92292 29837'
        site.contact_email = 'info@rntmpl.com'
        site.address = 'India'
        site.facebook_url = 'https://www.facebook.com/'
        site.instagram_url = 'https://www.instagram.com/'
        site.youtube_url = 'https://www.youtube.com/'
        site.registration_open = True
        site.registration_fee = 1499
        site.footer_text = 'All Rights Reserved.'
        site.save()

        static_images = Path(settings.BASE_DIR) / 'static' / 'website' / 'images'
        media_root = Path(settings.BASE_DIR) / 'media' / 'website'

        self._assign_file(site, 'logo', static_images / 'logo.png', save=False)
        self._assign_file(site, 'favicon', static_images / 'favicon.png', save=False)
        self._assign_file(site, 'default_share_image', static_images / 'blog6.jpg', save=False)
        self._assign_file(site, 'brochure_english', media_root / 'brochures' / 'rntmpl-company-profile-english.pdf', save=False)
        self._assign_file(site, 'brochure_hindi', media_root / 'brochures' / 'rntmpl-company-profile-hindi.pdf', save=False)
        site.save()

        home, _ = HomePage.objects.get_or_create(pk=1)
        home.eyebrow = 'Cricket We Love You'
        home.hero_title = 'Practice With A Purpose Play With A Passion'
        home.hero_description = (
            'Register for RNTMPL, build your verified player profile and begin '
            'your journey from professional trials to competitive cricket.'
        )
        home.primary_button_text = 'Register As Player'
        home.primary_button_url = '/register-player/'
        home.secondary_button_text = 'Explore League'
        home.secondary_button_url = '/match-center/'
        home.about_title = 'From Local Grounds To The Big Stage'
        home.about_description = (
            'RNTMPL provides grassroots players a structured pathway through '
            'online registration, trials, selection, teams, tournaments and auctions.'
        )
        home.registration_title = 'Your Cricket Journey Starts Here'
        home.registration_description = (
            'Complete your player registration, pay securely and track your '
            'trial and selection status from your personal dashboard.'
        )
        self._assign_file(home, 'hero_image', static_images / 'cricket-video.jpg', save=False)
        self._assign_file(home, 'about_image', static_images / 'abt1.png', save=False)
        home.is_published = True
        home.save()

        slide_assets = [
            (
                'Cricket Pathway',
                'Register, verify your profile and enter the structured player journey.',
                media_root / 'hero' / 'slides' / 'cricket-pathway.jpg',
                'Register As Player',
                '/register-player/',
            ),
            (
                'Competitive Cricket',
                'Step into professional trials, teams, tournaments and match exposure.',
                media_root / 'hero' / 'slides' / 'competitive-cricket.jpg',
                'Explore League',
                '/events/',
            ),
            (
                'Player Opportunity',
                'Build your cricket profile and track selection progress on one platform.',
                media_root / 'hero' / 'slides' / 'player-opportunity.jpg',
                'View Dashboard',
                '/accounts/dashboard/',
            ),
        ]
        for sort_order, (title, description, image_path, button_text, button_url) in enumerate(slide_assets, 1):
            slide, created = HeroSlide.objects.get_or_create(
                title=title,
                defaults={
                    'eyebrow': 'RNTMPL',
                    'description': description,
                    'primary_button_text': button_text,
                    'primary_button_url': button_url,
                    'secondary_button_text': 'Contact Us',
                    'secondary_button_url': '/contact/',
                    'sort_order': sort_order,
                    'is_active': True,
                },
            )
            if created or not slide.image:
                self._assign_file(slide, 'image', image_path)

        features = [
            ('Online Registration', 'Create your verified cricket identity and submit your application online.', 'icon-user-plus'),
            ('Professional Trials', 'Receive trial venue, schedule, check-in and selection updates.', 'icon-map-pin'),
            ('Secure Payment', 'Pay registration fees securely and receive instant confirmation.', 'icon-credit-card'),
            ('Player Dashboard', 'Track profile, documents, payment and application status.', 'icon-layout'),
            ('Competitive Cricket', 'Progress into teams, tournaments, live matches and auctions.', 'icon-award'),
            ('Performance Records', 'Build career statistics, rankings, achievements and your cricket resume.', 'icon-trending-up'),
        ]
        for order, (title, description, icon) in enumerate(features, 1):
            WebsiteFeature.objects.update_or_create(
                title=title,
                defaults={
                    'description': description,
                    'icon': icon,
                    'sort_order': order,
                    'is_active': True,
                },
            )

        gallery_files = ['crick1.jpg', 'crick2.jpg', 'crick3.jpg', 'crick4.jpg', 'cricks1.jpg']
        for order, filename in enumerate(gallery_files, 1):
            item, created = GalleryItem.objects.get_or_create(
                title=f'RNTMPL Cricket {order}',
                defaults={'sort_order': order, 'is_active': True},
            )
            image_path = static_images / filename
            if created and image_path.exists():
                with image_path.open('rb') as image:
                    item.image.save(filename, File(image), save=True)

        news = [
            ('RNTMPL Player Registrations Open', 'Online player registrations for the upcoming RNTMPL season are now open.', 'blog6.jpg'),
            ('Professional Cricket Trials Announced', 'Registered players will receive trial city, date and reporting details on their dashboard.', 'blog5.jpg'),
            ('Build Your Verified Cricket Profile', 'Players can maintain documents, performance records and selection status in one place.', 'blog4.jpg'),
        ]
        for index, (title, excerpt, image_name) in enumerate(news):
            post, created = NewsPost.objects.get_or_create(
                slug=title.lower().replace(' ', '-'),
                defaults={
                    'title': title,
                    'excerpt': excerpt,
                    'content': excerpt,
                    'published_at': timezone.now() - timedelta(days=index),
                    'is_published': True,
                },
            )
            image_path = static_images / image_name
            if created and image_path.exists():
                with image_path.open('rb') as image:
                    post.featured_image.save(image_name, File(image), save=True)

        page_image_map = [
            (GalleryPageSettings, 'banner_image', static_images / 'gallery4.jpg'),
            (BlogSettings, 'listing_banner_image', static_images / 'blog-d.jpg'),
            (NewsPageSettings, 'banner_image', static_images / 'blog6.jpg'),
            (ContactPageSettings, 'banner_image', static_images / 'crick2.jpg'),
            (EventPageSettings, 'banner_image', static_images / 'event-details.jpg'),
            (PartnerPageSettings, 'banner_image', static_images / 'league1.jpg'),
            (SponsorPageSettings, 'banner_image', static_images / 'league2.jpg'),
            (CareerPageSettings, 'banner_image', static_images / 'team-m4.jpg'),
            (AboutPageSettings, 'banner_image', static_images / 'abt2.png'),
            (TeamPageSettings, 'banner_image', static_images / 'team1.png'),
            (FAQPageSettings, 'banner_image', static_images / 'faq-ques.png'),
        ]
        for model_class, field_name, image_path in page_image_map:
            instance, _ = model_class.objects.get_or_create(pk=1)
            self._assign_file(instance, field_name, image_path)

        about_page = AboutPageSettings.objects.get(pk=1)
        self._assign_file(about_page, 'founder_image', static_images / 'player1.png')

        self.stdout.write(self.style.SUCCESS('Website CMS data seeded successfully.'))
