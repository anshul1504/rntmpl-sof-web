from django.urls import path

from apps.publicsite import views

app_name = 'publicsite'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('robots.txt', views.robots_txt, name='robots'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('blogs/', views.BlogListView.as_view(), name='blog-list'),
    path('blogs/<slug:slug>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('news/', views.NewsListView.as_view(), name='news-list'),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
    path('faq/', views.FAQPageView.as_view(), name='faq'),
    path('policies/<slug:page_type>/', views.PublicContentPageView.as_view(), name='public-content'),
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('partners/', views.PartnerPageView.as_view(), name='partners'),
    path('sponsors/', views.SponsorPageView.as_view(), name='sponsors'),
    path('careers/', views.CareerPageView.as_view(), name='careers'),
    path('careers/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('our-teams/', views.TeamListView.as_view(), name='team-list'),
    path('our-teams/<str:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('gallery/', views.GalleryPageView.as_view(), name='gallery'),
    path('guest/', views.GuestWelcomeView.as_view(), name='guest-welcome'),
    path('join/', views.RegistrationChoiceView.as_view(), name='registration-choice'),
    path('organizer-signup/', views.OrganizerSignupView.as_view(), name='organizer-signup'),
    path('organizer-applications/', views.OrganizerApplicationStatusView.as_view(), name='organizer-application-status'),
    path('player-journey/<int:step>/', views.PlayerJourneyView.as_view(), name='player-journey'),
    path('player-journey/review/', views.PlayerJourneyReviewView.as_view(), name='player-journey-review'),
    path('player-registration/payment/', views.PlayerPaymentView.as_view(), name='player-payment'),
    path('player-registration/payment/verify/', views.PlayerPaymentVerifyView.as_view(), name='player-payment-verify'),
    path('payments/razorpay/webhook/', views.RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('register-player/', views.player_registration_entry, name='player-registration'),
    path('live-scores/', views.PublicLiveScoreView.as_view(), name='live-scores'),
    path('match-center/', views.PublicMatchCenterView.as_view(), name='match-center'),
    path('events/<slug:slug>/', views.PublicTournamentView.as_view(), name='tournament-detail'),
    path('matches/<str:pk>/', views.PublicScorecardView.as_view(), name='scorecard'),
]
