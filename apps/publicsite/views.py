from datetime import timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.accounts.forms import OrganizerApplicationForm
from apps.accounts.models import OrganizerApplication, PaymentLedger, PaymentWebhookEvent
from apps.accounts.saas import (
    create_organizer_plan_payment,
    enqueue_notification,
    process_razorpay_payment_captured,
)
from apps.scoring.models import BatterInnings, BowlerFigures, Innings, MatchState
from apps.tournaments.models import (
    Tournament,
    TournamentGroup,
    TournamentMatch,
    TournamentPointsTable,
)
from apps.players.models import PlayerProfile
from apps.teams.models import (
    Team, TeamAchievement, TeamCategory, TeamRanking, TeamSeason, TeamSponsorship,
    TeamSquad, TeamStaff, TeamStat,
)
from apps.publicsite.models import (
    AboutLeader, AboutPageSettings, AboutValue,
    BlogSettings, CareerPageSettings, ContactFAQ, ContactPageSettings,
    ContactSubmission, EventPageSettings, GalleryItem, GalleryPageSettings,
    PlayerRegistrationApplication, PlayerPaymentTransaction,
    HeroSlide, HomePage, JobApplication, JobOpening,
    NewsPageSettings, NewsPost, PartnerEnquiry, PartnerFAQ, PartnerLogo,
    PartnerOpportunity, PartnerPageSettings, PublicContentPage, PublicFAQ,
    FAQPageSettings, SponsorEnquiry, SponsorInventory,
    SponsorLogo, SponsorPackage, SponsorPageSettings, TeamPageSettings,
    Testimonial, WebsiteFeature, WebsiteSettings,
)
from apps.publicsite.forms import (
    ContactSubmissionForm,
    JobApplicationForm,
    PartnerEnquiryForm,
    SponsorEnquiryForm, PlayerJourneyPersonalForm, PlayerJourneyCricketForm,
    PlayerJourneyExperienceForm, PaymentReferenceForm,
)
from apps.publicsite.payments import (
    RazorpayPaymentService,
    razorpay_is_configured,
    verify_razorpay_webhook_signature,
)


class HomePageView(TemplateView):
    template_name = 'website/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['hero_slides'] = HeroSlide.objects.filter(is_active=True)
        context['features'] = WebsiteFeature.objects.filter(is_active=True).order_by('sort_order', 'id')[:5]
        context['gallery_items'] = GalleryItem.objects.filter(is_active=True)[:5]
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:6]
        context['news_posts'] = NewsPost.objects.filter(is_published=True, content_type='BLOG')[:3]
        context['home_teams'] = Team.objects.filter(is_active=True, is_deleted=False, tenant__is_deleted=False, tenant__is_public=True).select_related('team_category', 'team_type').order_by('name')[:4]
        context['partner_logos'] = PartnerLogo.objects.filter(is_active=True)[:8]
        context['blog_settings'] = BlogSettings.objects.first() or BlogSettings()
        context['featured_tournaments'] = Tournament.objects.filter(
            is_deleted=False, tenant__is_deleted=False, tenant__is_public=True,
        ).select_related('tenant').order_by('-is_featured', '-start_date')[:4]
        context['upcoming_matches'] = TournamentMatch.objects.filter(
            is_deleted=False, is_completed=False,
            tournament__tenant__is_public=True,
        ).select_related('tournament', 'home_team__team', 'away_team__team').order_by('match_date')[:4]
        return context


class AboutPageView(TemplateView):
    template_name = 'website/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['about_page'] = AboutPageSettings.objects.first() or AboutPageSettings()
        context['values'] = AboutValue.objects.filter(is_active=True)
        context['leaders'] = AboutLeader.objects.filter(is_active=True)
        context['teams'] = Team.objects.filter(
            is_active=True, is_deleted=False,
            tenant__is_deleted=False, tenant__is_public=True,
        ).select_related('team_category', 'team_type').order_by('name')[:4]
        context['team_count'] = Team.objects.filter(
            is_active=True, is_deleted=False,
            tenant__is_deleted=False, tenant__is_public=True,
        ).count()
        context['player_count'] = TeamSquad.objects.filter(
            is_active=True, is_deleted=False,
            team_season__team__tenant__is_public=True,
        ).values('player_id').distinct().count()
        context['event_count'] = Tournament.objects.filter(
            is_deleted=False, tenant__is_deleted=False, tenant__is_public=True,
        ).count()
        return context


class BlogListView(ListView):
    model = NewsPost
    template_name = 'website/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        return NewsPost.objects.filter(is_published=True, content_type='BLOG').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['blog_settings'] = BlogSettings.objects.first() or BlogSettings()
        return context


class BlogDetailView(DetailView):
    model = NewsPost
    template_name = 'website/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return NewsPost.objects.filter(is_published=True, content_type='BLOG').prefetch_related('gallery_images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['blog_settings'] = BlogSettings.objects.first() or BlogSettings()
        context['related_posts'] = NewsPost.objects.filter(
            is_published=True, content_type='BLOG',
        ).exclude(pk=self.object.pk).order_by('-published_at')[:3]
        return context


class NewsListView(ListView):
    model = NewsPost
    template_name = 'website/news_list.html'
    context_object_name = 'news_items'
    paginate_by = 9

    def get_queryset(self):
        return NewsPost.objects.filter(is_published=True, content_type='NEWS').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['news_page'] = NewsPageSettings.objects.first() or NewsPageSettings()
        return context


class ContactPageView(FormView):
    template_name = 'website/contact.html'
    form_class = ContactSubmissionForm
    success_url = reverse_lazy('publicsite:contact')

    def form_valid(self, form):
        recent_duplicate = ContactSubmission.objects.filter(
            email__iexact=form.cleaned_data['email'],
            subject__endswith=form.cleaned_data['subject'],
            created_at__gte=timezone.now() - timedelta(minutes=2),
        ).exists()
        if recent_duplicate:
            form.add_error(None, 'This message was already submitted recently. Please wait before trying again.')
            return self.form_invalid(form)
        form.save()
        messages.success(self.request, 'Thank you. Your message has been submitted successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['contact_page'] = ContactPageSettings.objects.first() or ContactPageSettings()
        context['contact_faqs'] = ContactFAQ.objects.filter(is_active=True)
        return context


class EventListView(ListView):
    model = Tournament
    template_name = 'website/event_list.html'
    context_object_name = 'events'
    paginate_by = 9

    def get_queryset(self):
        queryset = Tournament.objects.filter(
            is_deleted=False,
            tenant__is_deleted=False,
            tenant__is_public=True,
        ).select_related('tenant', 'format').order_by('-is_featured', '-start_date', '-created_at')
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(city__icontains=search)
                | Q(state__icontains=search)
                | Q(venue__icontains=search)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['event_page'] = EventPageSettings.objects.first() or EventPageSettings()
        context['search_query'] = self.request.GET.get('search', '').strip()
        context['status_filter'] = self.request.GET.get('status', '').strip()
        context['status_choices'] = Tournament.Status.choices
        return context


class PartnerPageView(FormView):
    template_name = 'website/partners.html'
    form_class = PartnerEnquiryForm
    success_url = reverse_lazy('publicsite:partners')

    def form_valid(self, form):
        recent_duplicate = PartnerEnquiry.objects.filter(
            email__iexact=form.cleaned_data['email'],
            organisation_name__iexact=form.cleaned_data['organisation_name'],
            created_at__gte=timezone.now() - timedelta(minutes=5),
        ).exists()
        if recent_duplicate:
            form.add_error(None, 'This partnership enquiry was submitted recently. Please wait before trying again.')
            return self.form_invalid(form)
        form.save()
        messages.success(self.request, 'Thank you. Your partnership enquiry has been submitted.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['partner_page'] = PartnerPageSettings.objects.first() or PartnerPageSettings()
        context['partner_opportunities'] = PartnerOpportunity.objects.filter(is_active=True)
        context['partner_logos'] = PartnerLogo.objects.filter(is_active=True)
        context['partner_faqs'] = PartnerFAQ.objects.filter(is_active=True)
        return context


class SponsorPageView(FormView):
    template_name = 'website/sponsors.html'
    form_class = SponsorEnquiryForm
    success_url = reverse_lazy('publicsite:sponsors')

    def form_valid(self, form):
        recent_duplicate = SponsorEnquiry.objects.filter(
            email__iexact=form.cleaned_data['email'],
            company_name__iexact=form.cleaned_data['company_name'],
            created_at__gte=timezone.now() - timedelta(minutes=5),
        ).exists()
        if recent_duplicate:
            form.add_error(None, 'This sponsorship enquiry was submitted recently. Please wait before trying again.')
            return self.form_invalid(form)
        form.save()
        messages.success(self.request, 'Thank you. Your sponsorship enquiry has been submitted.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['sponsor_page'] = SponsorPageSettings.objects.first() or SponsorPageSettings()
        context['sponsor_packages'] = SponsorPackage.objects.filter(is_active=True)
        context['sponsor_inventory'] = SponsorInventory.objects.filter(is_active=True)
        context['sponsor_logos'] = SponsorLogo.objects.filter(is_active=True)
        return context


class CareerPageView(TemplateView):
    template_name = 'website/careers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['career_page'] = CareerPageSettings.objects.first() or CareerPageSettings()
        context['job_openings'] = JobOpening.objects.filter(is_active=True)
        return context


class TeamListView(ListView):
    model = Team
    template_name = 'website/team_list.html'
    context_object_name = 'teams'
    paginate_by = 12

    def get_queryset(self):
        queryset = Team.objects.filter(
            is_active=True, is_deleted=False,
            tenant__is_deleted=False, tenant__is_public=True,
        ).select_related('tenant', 'team_category', 'team_type').order_by('name')
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(short_name__icontains=search)
                | Q(city__icontains=search) | Q(home_ground__icontains=search)
            )
        category = self.request.GET.get('category', '').strip()
        if category:
            queryset = queryset.filter(team_category_id=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['team_page'] = TeamPageSettings.objects.first() or TeamPageSettings()
        context['team_categories'] = TeamCategory.objects.order_by('name')
        context['search_query'] = self.request.GET.get('search', '').strip()
        context['category_filter'] = self.request.GET.get('category', '').strip()
        return context


class TeamDetailView(DetailView):
    model = Team
    template_name = 'website/team_detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        return Team.objects.filter(
            is_active=True, is_deleted=False,
            tenant__is_deleted=False, tenant__is_public=True,
        ).select_related('tenant', 'team_category', 'team_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['team_page'] = TeamPageSettings.objects.first() or TeamPageSettings()
        season = TeamSeason.objects.filter(team=self.object, is_active=True, is_deleted=False).order_by('-year').first()
        context['team_season'] = season
        context['squad'] = TeamSquad.objects.filter(team_season=season, is_active=True, is_deleted=False).select_related('player') if season else TeamSquad.objects.none()
        context['staff'] = TeamStaff.objects.filter(team_season=season, is_active=True, is_deleted=False) if season else TeamStaff.objects.none()
        context['stats'] = TeamStat.objects.filter(team=self.object, is_deleted=False).order_by('-matches_played').first()
        context['achievements'] = TeamAchievement.objects.filter(
            team=self.object, is_deleted=False,
        ).select_related('tournament')[:8]
        context['sponsors'] = TeamSponsorship.objects.filter(
            team=self.object, is_active=True, is_deleted=False,
        )[:8]
        context['rankings'] = TeamRanking.objects.filter(
            team=self.object, is_deleted=False,
        ).order_by('rank')[:6]
        context['related_teams'] = Team.objects.filter(
            is_active=True, is_deleted=False,
            tenant__is_deleted=False, tenant__is_public=True,
        ).exclude(pk=self.object.pk).select_related(
            'team_category', 'team_type',
        ).order_by('name')[:3]
        return context


class JobDetailView(FormView):
    template_name = 'website/job_detail.html'
    form_class = JobApplicationForm

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(JobOpening, pk=kwargs['pk'], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('publicsite:job-detail', kwargs={'pk': self.job.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['job'] = self.job
        return initial

    def form_valid(self, form):
        form.instance.job = self.job
        recent_duplicate = JobApplication.objects.filter(
            email__iexact=form.cleaned_data['email'],
            job=self.job,
            created_at__gte=timezone.now() - timedelta(minutes=10),
        ).exists()
        if recent_duplicate:
            form.add_error(None, 'An application for this role was submitted recently.')
            return self.form_invalid(form)
        form.save()
        messages.success(self.request, 'Thank you. Your application has been submitted.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['career_page'] = CareerPageSettings.objects.first() or CareerPageSettings()
        context['job'] = self.job
        context['related_jobs'] = JobOpening.objects.filter(
            is_active=True,
        ).exclude(pk=self.job.pk).order_by('sort_order', '-created_at')[:3]
        return context


class GalleryPageView(ListView):
    model = GalleryItem
    template_name = 'website/gallery.html'
    context_object_name = 'gallery_items'
    paginate_by = 9

    def get_queryset(self):
        queryset = GalleryItem.objects.filter(is_active=True).order_by('-is_featured', 'sort_order', 'id')
        category = self.request.GET.get('category', '').strip()
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['gallery_page'] = GalleryPageSettings.objects.first() or GalleryPageSettings()
        context['category_filter'] = self.request.GET.get('category', '').strip()
        context['category_choices'] = GalleryItem.CATEGORY_CHOICES
        return context


class FAQPageView(TemplateView):
    template_name = 'website/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['faq_page'] = FAQPageSettings.objects.first() or FAQPageSettings()
        context['faqs'] = PublicFAQ.objects.filter(is_active=True)
        context['faq_categories'] = PublicFAQ.CATEGORY_CHOICES
        return context


class PublicContentPageView(DetailView):
    model = PublicContentPage
    template_name = 'website/public_content_page.html'
    context_object_name = 'content_page'
    slug_field = 'page_type'
    slug_url_kwarg = 'page_type'

    def get_queryset(self):
        return PublicContentPage.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        return context


PLAYER_JOURNEY_FORMS = {
    1: PlayerJourneyPersonalForm,
    2: PlayerJourneyCricketForm,
    3: PlayerJourneyExperienceForm,
}


class GuestWelcomeView(TemplateView):
    template_name = 'website/guest_welcome.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        return context


class RegistrationChoiceView(GuestWelcomeView):
    template_name = 'website/registration_choice.html'


class OrganizerSignupView(LoginRequiredMixin, FormView):
    form_class = OrganizerApplicationForm
    template_name = 'website/organizer_signup.html'
    success_url = reverse_lazy('publicsite:organizer-application-status')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            application = form.save(commit=False)
            application.user = self.request.user
            application.save()
            if application.plan.price > 0:
                create_organizer_plan_payment(application)
            enqueue_notification(
                event_type='organizer.application.submitted',
                recipient=application.email,
                user=self.request.user,
                subject='RNT MPL organizer application received',
                body='Your organizer application has been submitted for review.',
                payload={
                    'application_id': application.pk,
                    'plan': application.plan.code,
                },
            )
        messages.success(
            self.request,
            'Organizer application submitted. Our platform team will review it and provision your organization.',
        )
        return super().form_valid(form)


class OrganizerApplicationStatusView(LoginRequiredMixin, ListView):
    model = OrganizerApplication
    template_name = 'website/organizer_application_status.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return (
            OrganizerApplication.objects.filter(user=self.request.user)
            .select_related('plan', 'tenant', 'subscription')
            .prefetch_related('payment_ledger')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['pending_payments'] = PaymentLedger.objects.filter(
            user=self.request.user,
            purpose=PaymentLedger.Purpose.ORGANIZER_PLAN,
            status__in=[PaymentLedger.Status.CREATED, PaymentLedger.Status.PENDING],
        ).select_related('organizer_application', 'organizer_application__plan')
        return context


class PlayerJourneyView(View):
    template_name = 'website/player_journey.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def _context(self, form, step):
        return {
            'form': form, 'step': step, 'progress': step * 25,
            'site': WebsiteSettings.objects.first() or WebsiteSettings(),
            'page': HomePage.objects.filter(is_published=True).first() or HomePage(),
        }

    def get(self, request, step=1):
        if step not in PLAYER_JOURNEY_FORMS:
            return redirect('publicsite:player-journey', step=1)
        data = request.session.get('player_journey', {})
        form = PLAYER_JOURNEY_FORMS[step](initial=data)
        return render(request, self.template_name, self._context(form, step))

    def post(self, request, step=1):
        if step not in PLAYER_JOURNEY_FORMS:
            return redirect('publicsite:player-journey', step=1)
        form = PLAYER_JOURNEY_FORMS[step](request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form, step))
        data = request.session.get('player_journey', {})
        for key, value in form.cleaned_data.items():
            data[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value) if value is not None else ''
        request.session['player_journey'] = data
        request.session.modified = True
        if step < 3:
            return redirect('publicsite:player-journey', step=step + 1)
        return redirect('publicsite:player-journey-review')


class PlayerJourneyReviewView(GuestWelcomeView):
    template_name = 'website/player_journey_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['journey'] = self.request.session.get('player_journey', {})
        if not context['journey']:
            context['missing_journey'] = True
        return context

    def post(self, request, *args, **kwargs):
        data = request.session.get('player_journey')
        if not data:
            return redirect('publicsite:player-journey', step=1)
        request.session['registration_type'] = 'PLAYER'
        return redirect('accounts:register')


class PlayerPaymentView(FormView):
    template_name = 'website/player_payment.html'
    form_class = PaymentReferenceForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        self.application = get_object_or_404(PlayerRegistrationApplication, user=request.user)
        if self.application.payment_status in {
            PlayerRegistrationApplication.PaymentStatus.SUBMITTED,
            PlayerRegistrationApplication.PaymentStatus.VERIFIED,
        }:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['application'] = self.application
        context['razorpay_enabled'] = razorpay_is_configured()
        if context['razorpay_enabled']:
            try:
                payment = self._get_or_create_razorpay_order()
                context.update({
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'razorpay_order_id': payment.gateway_order_id,
                    'razorpay_amount': int(payment.amount * 100),
                    'razorpay_currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
                    'razorpay_verify_url': reverse('publicsite:player-payment-verify'),
                })
            except Exception as exc:
                context['razorpay_enabled'] = False
                messages.error(
                    self.request,
                    f'Payment gateway is temporarily unavailable: {exc}'
                )
        return context

    def _get_or_create_razorpay_order(self):
        existing = self.application.payments.filter(
            provider=PlayerPaymentTransaction.Provider.RAZORPAY,
            status=PlayerPaymentTransaction.Status.CREATED,
        ).order_by('-submitted_at').first()
        if existing:
            return existing
        receipt = f'player-{self.application.pk}-{timezone.now():%Y%m%d%H%M%S}'
        order = RazorpayPaymentService.create_order(
            amount=self.application.fee_amount,
            receipt=receipt,
            notes={
                'application_id': str(self.application.pk),
                'player': self.application.full_name,
                'email': self.application.email or self.request.user.email,
            },
        )
        order_id = order['id']
        return PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.request.user,
            amount=self.application.fee_amount,
            reference=order_id,
            provider=PlayerPaymentTransaction.Provider.RAZORPAY,
            gateway_order_id=order_id,
            gateway_payload=order,
            status=PlayerPaymentTransaction.Status.CREATED,
        )

    def form_valid(self, form):
        reference = form.cleaned_data['payment_reference']
        PlayerPaymentTransaction.objects.create(
            application=self.application,
            user=self.request.user,
            amount=self.application.fee_amount,
            reference=reference,
        )
        self.application.payment_reference = reference
        self.application.status = PlayerRegistrationApplication.Status.PAYMENT_SUBMITTED
        self.application.payment_status = (
            PlayerRegistrationApplication.PaymentStatus.SUBMITTED
        )
        self.application.save(
            update_fields=[
                'payment_reference', 'status', 'payment_status', 'updated_at'
            ]
        )
        messages.success(self.request, 'Payment reference submitted. Verification is pending.')
        return redirect('accounts:dashboard')


class PlayerPaymentVerifyView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        order_id = request.POST.get('razorpay_order_id', '').strip()
        payment_id = request.POST.get('razorpay_payment_id', '').strip()
        signature = request.POST.get('razorpay_signature', '').strip()
        payment = get_object_or_404(
            PlayerPaymentTransaction.objects.select_related('application', 'user'),
            user=request.user,
            provider=PlayerPaymentTransaction.Provider.RAZORPAY,
            gateway_order_id=order_id,
        )
        if not RazorpayPaymentService.verify_signature(
            order_id=order_id,
            payment_id=payment_id,
            signature=signature,
        ):
            payment.status = PlayerPaymentTransaction.Status.FAILED
            payment.gateway_payment_id = payment_id
            payment.gateway_signature = signature
            payment.save(update_fields=[
                'status', 'gateway_payment_id', 'gateway_signature'
            ])
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('publicsite:player-payment')

        with transaction.atomic():
            payment = PlayerPaymentTransaction.objects.select_for_update().get(pk=payment.pk)
            payment.status = PlayerPaymentTransaction.Status.VERIFIED
            payment.gateway_payment_id = payment_id
            payment.gateway_signature = signature
            payment.reviewed_at = timezone.now()
            payment.review_note = 'Verified automatically by Razorpay signature.'
            payment.save(update_fields=[
                'status', 'gateway_payment_id', 'gateway_signature',
                'reviewed_at', 'review_note'
            ])

            application = payment.application
            application.payment_reference = payment_id
            application.payment_status = PlayerRegistrationApplication.PaymentStatus.VERIFIED
            application.trial_status = PlayerRegistrationApplication.TrialStatus.ELIGIBLE
            application.status = PlayerRegistrationApplication.Status.PAYMENT_SUBMITTED
            application.save(update_fields=[
                'payment_reference', 'payment_status', 'trial_status',
                'status', 'updated_at'
            ])

            user = payment.user
            user.onboarding_state = user.OnboardingState.PLAYER_TRIAL_ELIGIBLE
            user.save(update_fields=['onboarding_state'])

        messages.success(request, 'Payment verified. Your trial dashboard is now unlocked.')
        return redirect('accounts:dashboard')


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    def post(self, request):
        signature = request.headers.get('X-Razorpay-Signature', '')
        raw_body = request.body
        if not verify_razorpay_webhook_signature(raw_body, signature):
            return HttpResponseBadRequest('Invalid signature')
        try:
            import json
            payload = json.loads(raw_body.decode('utf-8') or '{}')
        except ValueError:
            return HttpResponseBadRequest('Invalid JSON')

        event_type = payload.get('event', '')
        event_id = payload.get('id') or payload.get('event_id') or f'{event_type}:{payload.get("created_at", "")}'
        event, created = PaymentWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': payload,
                'signature': signature,
                'is_valid': True,
                'processed_at': timezone.now(),
            },
        )
        if not created:
            return JsonResponse({'status': 'duplicate', 'event_id': event.event_id})
        if event_type == 'payment.captured':
            try:
                processed_payment = process_razorpay_payment_captured(payload)
                if processed_payment:
                    event.processed_at = timezone.now()
                    event.save(update_fields=['processed_at', 'updated_at'])
            except Exception as exc:
                event.processing_error = str(exc)
                event.save(update_fields=['processing_error', 'updated_at'])
                return JsonResponse({'status': 'error', 'event_id': event.event_id}, status=500)

        return JsonResponse({'status': 'accepted', 'event_id': event.event_id})


def player_registration_entry(request):
    if request.user.is_authenticated:
        application = PlayerRegistrationApplication.objects.filter(user=request.user).first()
        if application and application.payment_status in {
            PlayerRegistrationApplication.PaymentStatus.NOT_STARTED,
            PlayerRegistrationApplication.PaymentStatus.PENDING,
            PlayerRegistrationApplication.PaymentStatus.REJECTED,
        }:
            return redirect('publicsite:player-payment')
        return redirect('accounts:dashboard')
    return redirect('publicsite:player-journey', step=1)


class PublicLiveScoreView(ListView):
    model = TournamentMatch
    template_name = 'publicsite/live_scores.html'
    context_object_name = 'live_matches'

    def get_queryset(self):
        return TournamentMatch.objects.filter(
            is_deleted=False,
            tournament__is_deleted=False,
            tournament__tenant__is_deleted=False,
            tournament__tenant__is_public=True,
            live_state__is_live=True,
        ).select_related(
            'tournament', 'tournament__format',
            'home_team__team', 'away_team__team',
            'live_state__batting_team__team', 'live_state__bowling_team__team',
            'live_state__striker', 'live_state__non_striker',
            'live_state__current_bowler',
        ).order_by('match_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['recent_results'] = TournamentMatch.objects.filter(
            is_deleted=False, is_completed=True,
            tournament__is_deleted=False,
            tournament__tenant__is_deleted=False,
            tournament__tenant__is_public=True,
        ).select_related(
            'tournament', 'home_team__team', 'away_team__team', 'winner__team',
        ).order_by('-match_date')[:4]
        context['upcoming_matches'] = TournamentMatch.objects.filter(
            is_deleted=False, is_completed=False,
            tournament__is_deleted=False,
            tournament__tenant__is_deleted=False,
            tournament__tenant__is_public=True,
        ).exclude(live_state__is_live=True).select_related(
            'tournament', 'home_team__team', 'away_team__team',
        ).order_by('match_date')[:4]
        return context


class PublicMatchCenterView(ListView):
    model = TournamentMatch
    template_name = 'publicsite/match_center.html'
    context_object_name = 'matches'
    paginate_by = 20

    def get_queryset(self):
        queryset = TournamentMatch.objects.filter(
            is_deleted=False,
            tournament__is_deleted=False,
            tournament__tenant__is_deleted=False,
            tournament__tenant__is_public=True,
        ).select_related(
            'tournament', 'tournament__tenant', 'home_team__team', 'away_team__team'
        ).order_by('-match_date')
        status = self.request.GET.get('status', '')
        if status == 'live':
            queryset = queryset.filter(live_state__is_live=True)
        elif status == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status == 'upcoming':
            queryset = queryset.filter(is_completed=False).exclude(live_state__is_live=True)
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(tournament__name__icontains=search)
                | Q(home_team__team__name__icontains=search)
                | Q(away_team__team__name__icontains=search)
                | Q(venue__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        base_matches = TournamentMatch.objects.filter(
            is_deleted=False, tournament__is_deleted=False,
            tournament__tenant__is_deleted=False, tournament__tenant__is_public=True,
        )
        context['live_count'] = base_matches.filter(live_state__is_live=True).count()
        context['upcoming_count'] = base_matches.filter(
            is_completed=False,
        ).exclude(live_state__is_live=True).count()
        context['completed_count'] = base_matches.filter(is_completed=True).count()
        context['featured_tournaments'] = Tournament.objects.filter(
            is_deleted=False,
            tenant__is_deleted=False,
            tenant__is_public=True,
        ).select_related('tenant').order_by('-is_featured', '-start_date')[:8]
        return context


class PublicTournamentView(DetailView):
    model = Tournament
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'website/event_detail.html'
    context_object_name = 'tournament'

    def get_queryset(self):
        return Tournament.objects.filter(
            is_deleted=False,
            tenant__is_deleted=False,
            tenant__is_public=True,
        ).select_related('tenant', 'format')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['event_page'] = EventPageSettings.objects.first() or EventPageSettings()
        tournament = self.object
        context['teams'] = tournament.tournamentteam_teams.filter(
            is_deleted=False
        ).select_related('team')
        context['matches'] = tournament.tournamentmatch_matches.filter(
            is_deleted=False
        ).select_related('home_team__team', 'away_team__team').order_by('match_date')
        groups = TournamentGroup.objects.filter(stage_instance__tournament=tournament)
        context['standings_by_group'] = [
            {
                'group': group,
                'standings': TournamentPointsTable.objects.filter(group=group)
                .select_related('team__team').order_by('position', '-points'),
            }
            for group in groups
        ]
        return context


class PublicScorecardView(DetailView):
    model = TournamentMatch
    template_name = 'publicsite/scorecard.html'
    context_object_name = 'match'

    def get_queryset(self):
        return TournamentMatch.objects.filter(
            is_deleted=False,
            tournament__is_deleted=False,
            tournament__tenant__is_deleted=False,
            tournament__tenant__is_public=True,
        ).select_related('tournament', 'home_team__team', 'away_team__team')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        innings_rows = []
        for innings in Innings.objects.filter(match=self.object).order_by('innings_number'):
            innings_rows.append({
                'innings': innings,
                'batting': BatterInnings.objects.filter(innings=innings)
                .select_related('player').order_by('batting_position'),
                'bowling': BowlerFigures.objects.filter(innings=innings)
                .select_related('player').order_by('bowling_order'),
            })
        context['innings_rows'] = innings_rows
        context['live_state'] = MatchState.objects.filter(match=self.object).select_related(
            'batting_team__team', 'bowling_team__team', 'striker', 'non_striker', 'current_bowler',
        ).first()
        context['site'] = WebsiteSettings.objects.first() or WebsiteSettings()
        context['page'] = HomePage.objects.filter(is_published=True).first() or HomePage()
        context['related_matches'] = TournamentMatch.objects.filter(
            tournament=self.object.tournament, is_deleted=False,
        ).exclude(pk=self.object.pk).select_related(
            'home_team__team', 'away_team__team',
        ).order_by('match_date')[:4]
        return context


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /website-admin/',
        'Disallow: /accounts/',
        f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def sitemap_xml(request):
    static_urls = [
        reverse('publicsite:home'), reverse('publicsite:about'),
        reverse('publicsite:blog-list'), reverse('publicsite:news-list'),
        reverse('publicsite:contact'), reverse('publicsite:faq'),
        reverse('publicsite:event-list'), reverse('publicsite:partners'),
        reverse('publicsite:sponsors'), reverse('publicsite:careers'),
        reverse('publicsite:team-list'), reverse('publicsite:gallery'),
        reverse('publicsite:live-scores'), reverse('publicsite:match-center'),
        reverse('publicsite:organizer-signup'),
    ]
    static_urls += [
        reverse('publicsite:public-content', kwargs={'page_type': slug})
        for slug in ('privacy-policy', 'terms-conditions', 'refund-policy', 'disclaimer')
    ]
    dynamic_urls = [
        reverse('publicsite:blog-detail', kwargs={'slug': slug})
        for slug in NewsPost.objects.filter(is_published=True, content_type='BLOG').values_list('slug', flat=True)
    ]
    dynamic_urls += [
        reverse('publicsite:team-detail', kwargs={'pk': pk})
        for pk in Team.objects.filter(is_active=True, is_deleted=False, tenant__is_public=True).values_list('pk', flat=True)
    ]
    dynamic_urls += [
        reverse('publicsite:tournament-detail', kwargs={'slug': slug})
        for slug in Tournament.objects.filter(is_deleted=False, tenant__is_public=True).values_list('slug', flat=True)
    ]
    base = f'{request.scheme}://{request.get_host()}'
    rows = ''.join(f'<url><loc>{base}{url}</loc></url>' for url in static_urls + dynamic_urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>'
    return HttpResponse(xml, content_type='application/xml')


def public_404(request, exception):
    context = {
        'site': WebsiteSettings.objects.first() or WebsiteSettings(),
        'page': HomePage.objects.filter(is_published=True).first() or HomePage(),
    }
    return render(request, 'website/404.html', context, status=404)


def public_500(request):
    context = {
        'site': WebsiteSettings.objects.first() or WebsiteSettings(),
        'page': HomePage.objects.filter(is_published=True).first() or HomePage(),
    }
    return render(request, 'website/500.html', context, status=500)
