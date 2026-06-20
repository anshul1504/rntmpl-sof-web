from django.contrib import admin

from apps.publicsite.models import (
    AboutLeader,
    AboutPageSettings,
    AboutValue,
    BlogImage,
    BlogSettings,
    ContactPageSettings,
    ContactFAQ,
    EventPageSettings,
    ContactSubmission,
    CareerPageSettings,
    GalleryItem,
    GalleryPageSettings,
    HeroSlide,
    HomePage,
    JobApplication,
    JobOpening,
    NewsPost,
    NewsPageSettings,
    PartnerEnquiry,
    PartnerFAQ,
    PartnerLogo,
    PartnerOpportunity,
    PublicContentPage,
    PlayerRegistrationApplication,
    PublicFAQ,
    FAQPageSettings,
    PartnerPageSettings,
    SponsorEnquiry,
    SponsorInventory,
    SponsorLogo,
    SponsorPackage,
    SponsorPageSettings,
    TeamPageSettings,
    Testimonial,
    WebsiteFeature,
    WebsiteSettings,
)


class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AboutPageSettings)
class AboutPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Mission and Vision', {'fields': ('mission_title', 'mission_content', 'vision_title', 'vision_content')}),
        ('Founder', {'fields': ('founder_eyebrow', 'founder_name', 'founder_designation', 'founder_message', 'founder_image', 'founder_linkedin_url')}),
        ('Section Titles', {'fields': ('values_title', 'leadership_title', 'teams_title')}),
        ('Bottom CTA', {'fields': ('cta_title', 'cta_description', 'cta_button_text', 'cta_button_url')}),
    )


@admin.register(AboutValue)
class AboutValueAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'description')


@admin.register(AboutLeader)
class AboutLeaderAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name', 'designation', 'bio')


@admin.register(WebsiteSettings)
class WebsiteSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Brand', {'fields': ('site_name', 'tagline', 'announcement', 'logo', 'favicon')}),
        ('Registration', {'fields': ('registration_open', 'registration_fee')}),
        ('Contact', {'fields': ('contact_email', 'contact_phone', 'address')}),
        ('Social', {'fields': ('facebook_url', 'instagram_url', 'youtube_url')}),
        ('WhatsApp', {'fields': ('whatsapp_number', 'whatsapp_message')}),
        ('SEO Defaults', {'fields': ('default_meta_title', 'default_meta_description', 'default_share_image')}),
        ('Company Brochures', {'fields': ('brochure_english', 'brochure_hindi')}),
        ('Footer', {'fields': ('footer_text',)}),
    )


@admin.register(HomePage)
class HomePageAdmin(SingletonAdmin):
    fieldsets = (
        ('Fallback Hero', {'description': 'Used when no active Hero Slides exist.', 'fields': ('eyebrow', 'hero_title', 'hero_description', 'hero_image')}),
        ('Fallback Hero Actions', {'fields': ('primary_button_text', 'primary_button_url', 'secondary_button_text', 'secondary_button_url')}),
        ('About', {'fields': (
            'about_title', 'about_description', 'about_support_text', 'about_image',
            'about_point_one', 'about_point_two', 'about_point_three', 'about_point_four',
        )}),
        ('Player Pathway', {'fields': ('pathway_eyebrow', 'pathway_title', 'pathway_description')}),
        ('Teams and Events', {'fields': ('teams_eyebrow', 'teams_title', 'events_eyebrow', 'events_title', 'matches_eyebrow', 'matches_title')}),
        ('Opportunities and Gallery', {'fields': ('opportunities_eyebrow', 'opportunities_title', 'gallery_eyebrow', 'gallery_title')}),
        ('Testimonials', {'fields': ('testimonials_eyebrow', 'testimonials_title')}),
        ('Registration CTA', {'fields': ('registration_title', 'registration_description')}),
        ('Publishing', {'fields': ('is_published',)}),
    )


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    fieldsets = (
        ('Slide Image', {'fields': ('image',)}),
        ('Display', {'fields': ('sort_order', 'is_active')}),
    )


@admin.register(WebsiteFeature)
class WebsiteFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'event_name', 'captured_on', 'is_featured', 'sort_order', 'is_active')
    list_editable = ('is_featured', 'sort_order', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active', 'captured_on')
    search_fields = ('title', 'caption', 'event_name')
    date_hierarchy = 'captured_on'
    fieldsets = (
        ('Image', {'fields': ('title', 'image', 'caption')}),
        ('Details', {'fields': ('category', 'event_name', 'captured_on')}),
        ('Display', {'fields': ('is_featured', 'sort_order', 'is_active')}),
    )


@admin.register(GalleryPageSettings)
class GalleryPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Labels', {'fields': ('all_filter_text', 'empty_title', 'empty_description')}),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')


class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1
    fields = ('image', 'caption', 'sort_order')
    ordering = ('sort_order', 'id')


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'published_at', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('content_type', 'is_published', 'published_at')
    search_fields = ('title', 'excerpt', 'content')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Post Content', {'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')}),
        ('Publishing', {'fields': ('content_type', 'published_at', 'is_published')}),
    )
    inlines = (BlogImageInline,)


@admin.register(BlogSettings)
class BlogSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Homepage Blog Section', {'fields': ('eyebrow', 'homepage_title', 'homepage_description', 'view_all_text')}),
        ('Blog Listing', {'fields': ('listing_title', 'listing_banner_image', 'card_badge_text', 'read_more_text', 'empty_title')}),
        ('Blog Detail', {'fields': (
            'detail_back_text', 'detail_category', 'detail_author_label',
            'gallery_eyebrow', 'gallery_title', 'related_eyebrow', 'related_title',
            'detail_cta_title', 'detail_cta_button_text',
        )}),
    )


@admin.register(NewsPageSettings)
class NewsPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Labels', {'fields': ('read_more_text', 'empty_title', 'detail_back_text', 'related_title')}),
    )


@admin.register(ContactPageSettings)
class ContactPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Contact Form', {'fields': ('form_title', 'office_hours', 'response_time')}),
        ('WhatsApp', {'fields': ('whatsapp_title', 'whatsapp_description')}),
        ('Bottom CTA', {'fields': ('cta_title', 'cta_description')}),
        ('Location', {'fields': ('map_embed_url',)}),
    )


@admin.register(ContactFAQ)
class ContactFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('question', 'answer')


@admin.register(EventPageSettings)
class EventPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Filters', {'fields': ('search_placeholder', 'all_statuses_text', 'filter_button_text', 'reset_button_text')}),
        ('Event Cards', {'fields': (
            'featured_badge_text', 'view_event_text', 'prize_label',
            'teams_label', 'matches_label', 'players_label',
        )}),
        ('Event Detail', {'fields': (
            'detail_back_text', 'overview_eyebrow', 'overview_title',
            'fixtures_eyebrow', 'fixtures_title', 'teams_eyebrow', 'teams_title',
            'fixtures_empty_text', 'teams_empty_text',
        )}),
        ('Empty State', {'fields': ('empty_title', 'empty_description')}),
    )


@admin.register(PartnerPageSettings)
class PartnerPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Partnership Benefits', {'fields': ('benefits_title', 'benefit_one', 'benefit_two', 'benefit_three', 'benefit_four')}),
        ('Section Titles', {'fields': ('opportunities_title', 'process_title', 'faq_title')}),
        ('Form', {'fields': ('form_title',)}),
    )


@admin.register(PartnerOpportunity)
class PartnerOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'description')


@admin.register(PartnerLogo)
class PartnerLogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name',)


@admin.register(PartnerFAQ)
class PartnerFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('question', 'answer')


@admin.register(PartnerEnquiry)
class PartnerEnquiryAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'contact_person', 'partner_type', 'email', 'phone', 'city', 'created_at', 'is_contacted')
    list_editable = ('is_contacted',)
    list_filter = ('partner_type', 'is_contacted', 'created_at')
    search_fields = ('organisation_name', 'contact_person', 'email', 'phone', 'city', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('organisation_name', 'contact_person', 'email', 'phone', 'partner_type', 'website', 'city', 'message', 'created_at')


@admin.register(SponsorPageSettings)
class SponsorPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Section Titles', {'fields': ('packages_title', 'metrics_title', 'audience_title', 'inventory_title', 'process_title', 'form_title')}),
        ('Audience Metrics', {'fields': (
            'audience_metric', 'audience_label', 'players_metric', 'players_label',
            'events_metric', 'events_label', 'cities_metric', 'cities_label',
        )}),
    )


@admin.register(SponsorPackage)
class SponsorPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name', 'short_description', 'features')


@admin.register(SponsorInventory)
class SponsorInventoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'description')


@admin.register(SponsorLogo)
class SponsorLogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name',)


@admin.register(SponsorEnquiry)
class SponsorEnquiryAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'industry', 'budget_range', 'email', 'phone', 'created_at', 'is_contacted')
    list_editable = ('is_contacted',)
    list_filter = ('budget_range', 'is_contacted', 'created_at')
    search_fields = ('company_name', 'contact_person', 'industry', 'email', 'phone', 'objectives')
    date_hierarchy = 'created_at'
    readonly_fields = ('company_name', 'contact_person', 'email', 'phone', 'website', 'industry', 'budget_range', 'objectives', 'created_at')


@admin.register(CareerPageSettings)
class CareerPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Section Titles', {'fields': ('openings_title', 'benefits_title', 'process_title', 'form_title')}),
    )


@admin.register(TeamPageSettings)
class TeamPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Listing', {'fields': ('search_placeholder', 'all_categories_text', 'empty_title', 'empty_description')}),
        ('Team Detail', {'fields': ('detail_back_text', 'squad_title', 'staff_title', 'achievements_title')}),
    )


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'location', 'employment_type', 'application_deadline', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('department', 'employment_type', 'is_active', 'application_deadline')
    search_fields = ('title', 'department', 'location', 'summary', 'requirements')
    date_hierarchy = 'application_deadline'


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'phone', 'city', 'experience_years', 'created_at', 'is_reviewed')
    list_editable = ('is_reviewed',)
    list_filter = ('job', 'is_reviewed', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'city', 'current_role', 'cover_note')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'job', 'full_name', 'email', 'phone', 'city', 'experience_years',
        'current_role', 'linkedin_url', 'resume', 'cover_note', 'created_at',
    )


@admin.register(FAQPageSettings)
class FAQPageSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ('Page Header', {'fields': ('eyebrow', 'title', 'description', 'banner_image')}),
        ('Support CTA', {'fields': ('contact_title', 'contact_description')}),
    )


@admin.register(PublicFAQ)
class PublicFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')


@admin.register(PublicContentPage)
class PublicContentPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'page_type', 'updated_at', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('page_type', 'is_published')
    search_fields = ('title', 'summary', 'content')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Page', {'fields': ('page_type', 'eyebrow', 'title', 'summary', 'banner_image')}),
        ('Content', {'fields': ('content',)}),
        ('Publishing', {'fields': ('is_published', 'updated_at')}),
    )


@admin.register(PlayerRegistrationApplication)
class PlayerRegistrationApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'role', 'highest_level', 'fee_amount', 'status', 'created_at')
    list_filter = ('status', 'role', 'highest_level', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'payment_reference')
    readonly_fields = tuple(
        field.name for field in PlayerRegistrationApplication._meta.fields
        if field.name not in {'status', 'payment_reference'}
    )
    fields = tuple(field.name for field in PlayerRegistrationApplication._meta.fields)
    list_editable = ('status',)
    date_hierarchy = 'created_at'


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'created_at', 'is_resolved')
    list_editable = ('is_resolved',)
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
