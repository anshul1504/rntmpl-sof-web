from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.publicsite.models import (
    GalleryItem,
    HomePage,
    NewsPost,
    WebsiteFeature,
    WebsiteSettings,
)


class Command(BaseCommand):
    help = 'Seed the public website CMS with RNTMPL demo content and reference assets.'

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
        home.is_published = True
        home.save()

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

        static_images = Path(settings.BASE_DIR) / 'static' / 'website' / 'images'
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

        self.stdout.write(self.style.SUCCESS('Website CMS data seeded successfully.'))
