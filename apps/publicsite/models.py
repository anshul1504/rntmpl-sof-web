from django.db import models


class WebsiteSettings(models.Model):
    site_name = models.CharField(max_length=120, default='RNTMPL')
    tagline = models.CharField(max_length=255, default='Bharat Ka Cricket, Har Player Ka Sapna')
    announcement = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='website/logo/', blank=True, null=True)
    favicon = models.ImageField(upload_to='website/favicon/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, default='919229229837', help_text='Country code and number only, without + or spaces.')
    whatsapp_message = models.CharField(max_length=255, default='Hello RNTMPL, I want more information.')
    default_meta_title = models.CharField(max_length=160, blank=True, default='')
    default_meta_description = models.CharField(max_length=255, blank=True, default='')
    default_share_image = models.ImageField(upload_to='website/seo/', blank=True, null=True)
    brochure_english = models.FileField(upload_to='website/brochures/', blank=True, null=True)
    brochure_hindi = models.FileField(upload_to='website/brochures/', blank=True, null=True)
    registration_open = models.BooleanField(default=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=1499)
    footer_text = models.CharField(max_length=255, default='All Rights Reserved.')

    class Meta:
        verbose_name = 'Website Settings'
        verbose_name_plural = 'Website Settings'

    def __str__(self):
        return self.site_name


class HomePage(models.Model):
    eyebrow = models.CharField(max_length=120, default='Registrations Now Open')
    hero_title = models.CharField(max_length=255, default='Practice with purpose. Play with passion.')
    hero_description = models.TextField(default='A professional platform for grassroots cricket talent to register, compete and get discovered.')
    hero_image = models.ImageField(upload_to='website/hero/', blank=True, null=True)
    primary_button_text = models.CharField(max_length=60, default='Register as Player')
    primary_button_url = models.CharField(max_length=255, default='/accounts/register/')
    secondary_button_text = models.CharField(max_length=60, default='Explore League')
    secondary_button_url = models.CharField(max_length=255, default='/match-center/')
    about_title = models.CharField(max_length=255, default='From local grounds to the big stage')
    about_description = models.TextField(default='RNTMPL gives serious players a structured pathway through registration, trials, selection and competitive cricket.')
    about_image = models.ImageField(upload_to='website/about/', blank=True, null=True)
    about_support_text = models.TextField(default='From local grounds and raw talent to structured trials, professional competition and real recognition—RNTMPL gives every serious cricketer a platform to move forward.')
    about_point_one = models.CharField(max_length=120, default='Verified player identity')
    about_point_two = models.CharField(max_length=120, default='Professional trial pathway')
    about_point_three = models.CharField(max_length=120, default='Competitive match exposure')
    about_point_four = models.CharField(max_length=120, default='Transparent selection journey')
    registration_title = models.CharField(max_length=255, default='Your cricket journey starts here')
    registration_description = models.TextField(default='Complete your player profile, pay the registration fee securely and track your trial and selection status from your dashboard.')
    pathway_eyebrow = models.CharField(max_length=80, default='How RNTMPL Works')
    pathway_title = models.CharField(max_length=180, default='Your Journey From Registration To Recognition')
    pathway_description = models.TextField(default='One structured platform to create your cricket identity, attend verified trials, join teams and build a competitive playing record.')
    teams_eyebrow = models.CharField(max_length=80, default='League Teams')
    teams_title = models.CharField(max_length=180, default='Meet The Competition')
    events_eyebrow = models.CharField(max_length=80, default='Cricket Calendar')
    events_title = models.CharField(max_length=180, default='Upcoming Cricket Events')
    matches_eyebrow = models.CharField(max_length=80, default='Match Centre')
    matches_title = models.CharField(max_length=180, default='Upcoming Fixtures')
    opportunities_eyebrow = models.CharField(max_length=80, default='Work With Us')
    opportunities_title = models.CharField(max_length=180, default='Grow With The Cricket Ecosystem')
    gallery_eyebrow = models.CharField(max_length=80, default='RNTMPL Moments')
    gallery_title = models.CharField(max_length=180, default='Cricket In Action')
    testimonials_eyebrow = models.CharField(max_length=80, default='Community Voices')
    testimonials_title = models.CharField(max_length=180, default='What People Say')
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Home Page'
        verbose_name_plural = 'Home Page'

    def __str__(self):
        return 'Public Home Page'


class HeroSlide(models.Model):
    eyebrow = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='website/hero/slides/')
    primary_button_text = models.CharField(max_length=60, blank=True)
    primary_button_url = models.CharField(max_length=255, blank=True)
    secondary_button_text = models.CharField(max_length=60, blank=True)
    secondary_button_url = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title or f'Hero slide {self.pk or "new"}'


class WebsiteFeature(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    icon = models.CharField(max_length=60, default='icon-award')
    image = models.ImageField(upload_to='website/features/', blank=True, null=True)
    link_url = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class GalleryItem(models.Model):
    CATEGORY_CHOICES = (
        ('MATCH', 'Match Action'),
        ('TEAM', 'Teams'),
        ('TRIAL', 'Trials'),
        ('EVENT', 'Events'),
        ('BEHIND', 'Behind The Scenes'),
        ('OTHER', 'Other'),
    )
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to='website/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MATCH')
    event_name = models.CharField(max_length=120, blank=True)
    captured_on = models.DateField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title or f'Gallery image {self.pk}'


class GalleryPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='RNTMPL Moments')
    title = models.CharField(max_length=180, default='Cricket Gallery')
    description = models.TextField(default='Match action, team moments, trials and unforgettable scenes from the RNTMPL cricket journey.')
    banner_image = models.ImageField(upload_to='website/gallery/banner/', blank=True, null=True)
    all_filter_text = models.CharField(max_length=40, default='All Moments')
    empty_title = models.CharField(max_length=120, default='No gallery images found')
    empty_description = models.CharField(max_length=255, default='New cricket moments will be published soon.')

    class Meta:
        verbose_name = 'Gallery Page Settings'
        verbose_name_plural = 'Gallery Page Settings'

    def __str__(self):
        return 'Gallery Page Settings'


class Testimonial(models.Model):
    name = models.CharField(max_length=120)
    designation = models.CharField(max_length=120, blank=True)
    quote = models.TextField()
    photo = models.ImageField(upload_to='website/testimonials/', blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class NewsPost(models.Model):
    CONTENT_TYPE_CHOICES = (
        ('BLOG', 'Blog'),
        ('NEWS', 'News'),
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='website/news/', blank=True, null=True)
    published_at = models.DateTimeField()
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default='BLOG', db_index=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class BlogImage(models.Model):
    post = models.ForeignKey(NewsPost, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='website/news/gallery/')
    caption = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.caption or f'{self.post.title} image'


class BlogSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Blog & News')
    homepage_title = models.CharField(max_length=180, default='Latest From The Cricket World')
    homepage_description = models.TextField(default='Player stories, league announcements, trial updates and everything happening across the RNTMPL cricket ecosystem.')
    view_all_text = models.CharField(max_length=40, default='View All Blogs')
    listing_title = models.CharField(max_length=180, default='Cricket Stories & League Updates')
    listing_banner_image = models.ImageField(upload_to='website/blog/banner/', blank=True, null=True)
    detail_back_text = models.CharField(max_length=40, default='Back to Blogs')
    card_badge_text = models.CharField(max_length=40, default='RNTMPL News')
    read_more_text = models.CharField(max_length=40, default='Read Update')
    empty_title = models.CharField(max_length=120, default='No blogs published yet')
    detail_category = models.CharField(max_length=80, default='RNTMPL Cricket')
    detail_author_label = models.CharField(max_length=80, default='RNTMPL Editorial')
    gallery_eyebrow = models.CharField(max_length=80, default='Inside The Story')
    gallery_title = models.CharField(max_length=120, default='Photo Gallery')
    related_eyebrow = models.CharField(max_length=80, default='Keep Reading')
    related_title = models.CharField(max_length=120, default='Related Cricket Updates')
    detail_cta_title = models.CharField(max_length=180, default='Start Your Cricket Journey With RNTMPL')
    detail_cta_button_text = models.CharField(max_length=60, default='Register As Player')

    class Meta:
        verbose_name = 'Blog Settings'
        verbose_name_plural = 'Blog Settings'

    def __str__(self):
        return 'Blog Settings'


class NewsPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='RNTMPL Newsroom')
    title = models.CharField(max_length=180, default='Latest Cricket News')
    description = models.TextField(default='Official announcements, tournament updates, player news and important information from RNTMPL.')
    banner_image = models.ImageField(upload_to='website/news/banner/', blank=True, null=True)
    read_more_text = models.CharField(max_length=40, default='Read News')
    empty_title = models.CharField(max_length=120, default='No news published yet')
    detail_back_text = models.CharField(max_length=40, default='Back to News')
    related_title = models.CharField(max_length=120, default='More News')

    class Meta:
        verbose_name = 'News Page Settings'
        verbose_name_plural = 'News Page Settings'

    def __str__(self):
        return 'News Page Settings'


class ContactPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Contact RNTMPL')
    title = models.CharField(max_length=180, default='Let’s Talk Cricket')
    description = models.TextField(default='Questions about registration, trials, teams, partnerships or league operations? Send us a message and our team will connect with you.')
    banner_image = models.ImageField(upload_to='website/contact/banner/', blank=True, null=True)
    form_title = models.CharField(max_length=120, default='Send Us A Message')
    office_hours = models.CharField(max_length=120, default='Monday to Saturday, 10:00 AM – 6:00 PM')
    response_time = models.CharField(max_length=120, default='We usually respond within one business day.')
    map_embed_url = models.URLField(blank=True)
    whatsapp_title = models.CharField(max_length=120, default='Chat With Our Team')
    whatsapp_description = models.CharField(max_length=255, default='Need a quick answer about registration or trials? Connect with us directly on WhatsApp.')
    cta_title = models.CharField(max_length=180, default='Ready To Start Your Cricket Journey?')
    cta_description = models.CharField(max_length=255, default='Create your verified player profile and take the first step toward trials and competitive cricket.')

    class Meta:
        verbose_name = 'Contact Page Settings'
        verbose_name_plural = 'Contact Page Settings'

    def __str__(self):
        return 'Contact Page Settings'


class ContactFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Contact FAQ'
        verbose_name_plural = 'Contact FAQs'

    def __str__(self):
        return self.question


class EventPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='RNTMPL Events')
    title = models.CharField(max_length=180, default='Cricket Tournaments & Events')
    description = models.TextField(default='Explore upcoming tournaments, active competitions and completed RNTMPL cricket events.')
    banner_image = models.ImageField(upload_to='website/events/banner/', blank=True, null=True)
    empty_title = models.CharField(max_length=120, default='No events found')
    empty_description = models.CharField(max_length=255, default='New tournaments and cricket events will be announced soon.')
    search_placeholder = models.CharField(max_length=100, default='Search event or city')
    all_statuses_text = models.CharField(max_length=50, default='All Statuses')
    filter_button_text = models.CharField(max_length=40, default='Filter')
    reset_button_text = models.CharField(max_length=40, default='Reset')
    featured_badge_text = models.CharField(max_length=40, default='Featured')
    view_event_text = models.CharField(max_length=40, default='View Event')
    prize_label = models.CharField(max_length=40, default='Prize Pool')
    teams_label = models.CharField(max_length=30, default='Teams')
    matches_label = models.CharField(max_length=30, default='Matches')
    players_label = models.CharField(max_length=30, default='Players')
    detail_back_text = models.CharField(max_length=40, default='All Events')
    overview_eyebrow = models.CharField(max_length=80, default='Tournament Overview')
    overview_title = models.CharField(max_length=120, default='Event Information')
    fixtures_eyebrow = models.CharField(max_length=80, default='Schedule')
    fixtures_title = models.CharField(max_length=120, default='Fixtures & Results')
    teams_eyebrow = models.CharField(max_length=80, default='Participants')
    teams_title = models.CharField(max_length=120, default='Teams')
    fixtures_empty_text = models.CharField(max_length=120, default='Fixtures will be published soon.')
    teams_empty_text = models.CharField(max_length=120, default='Teams will be announced soon.')

    class Meta:
        verbose_name = 'Event Page Settings'
        verbose_name_plural = 'Event Page Settings'

    def __str__(self):
        return 'Event Page Settings'


class PartnerPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Partner With RNTMPL')
    title = models.CharField(max_length=180, default='Build The Future Of Cricket With Us')
    description = models.TextField(default='Collaborate with RNTMPL as a sponsor, academy, venue, media, technology or community partner.')
    banner_image = models.ImageField(upload_to='website/partners/banner/', blank=True, null=True)
    form_title = models.CharField(max_length=120, default='Start A Partnership Conversation')
    benefits_title = models.CharField(max_length=120, default='Why Partner With RNTMPL')
    benefit_one = models.CharField(max_length=160, default='Reach an active grassroots cricket audience')
    benefit_two = models.CharField(max_length=160, default='Build meaningful player and community engagement')
    benefit_three = models.CharField(max_length=160, default='Create measurable event and digital visibility')
    benefit_four = models.CharField(max_length=160, default='Collaborate through flexible partnership models')
    opportunities_title = models.CharField(max_length=120, default='Partnership Opportunities')
    process_title = models.CharField(max_length=120, default='How Partnership Works')
    faq_title = models.CharField(max_length=120, default='Partnership FAQs')

    class Meta:
        verbose_name = 'Partner Page Settings'
        verbose_name_plural = 'Partner Page Settings'

    def __str__(self):
        return 'Partner Page Settings'


class PartnerOpportunity(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField()
    icon = models.CharField(max_length=60, default='icon-star')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Partner Opportunity'
        verbose_name_plural = 'Partner Opportunities'

    def __str__(self):
        return self.title


class PartnerLogo(models.Model):
    name = models.CharField(max_length=120)
    logo = models.ImageField(upload_to='website/partners/logos/')
    website_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class PartnerFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Partner FAQ'
        verbose_name_plural = 'Partner FAQs'

    def __str__(self):
        return self.question


class SponsorPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Sponsor RNTMPL')
    title = models.CharField(max_length=180, default='Put Your Brand At The Heart Of Cricket')
    description = models.TextField(default='Connect your brand with players, teams, families and cricket audiences through meaningful RNTMPL sponsorship opportunities.')
    banner_image = models.ImageField(upload_to='website/sponsors/banner/', blank=True, null=True)
    packages_title = models.CharField(max_length=120, default='Sponsorship Packages')
    metrics_title = models.CharField(max_length=120, default='A Platform Built For Visibility')
    form_title = models.CharField(max_length=120, default='Request A Sponsorship Proposal')
    inventory_title = models.CharField(max_length=120, default='Where Your Brand Can Appear')
    process_title = models.CharField(max_length=120, default='From Brief To Brand Activation')
    audience_title = models.CharField(max_length=120, default='Connect With A Cricket-First Audience')
    audience_metric = models.CharField(max_length=40, default='10K+')
    audience_label = models.CharField(max_length=80, default='Cricket Audience')
    players_metric = models.CharField(max_length=40, default='1K+')
    players_label = models.CharField(max_length=80, default='Player Network')
    events_metric = models.CharField(max_length=40, default='25+')
    events_label = models.CharField(max_length=80, default='Event Opportunities')
    cities_metric = models.CharField(max_length=40, default='10+')
    cities_label = models.CharField(max_length=80, default='Target Cities')

    class Meta:
        verbose_name = 'Sponsor Page Settings'
        verbose_name_plural = 'Sponsor Page Settings'

    def __str__(self):
        return 'Sponsor Page Settings'


class SponsorPackage(models.Model):
    name = models.CharField(max_length=120)
    short_description = models.CharField(max_length=255)
    features = models.TextField(help_text='Enter one feature per line.')
    badge = models.CharField(max_length=40, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class SponsorInventory(models.Model):
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=60, default='icon-monitor')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Sponsor Inventory'
        verbose_name_plural = 'Sponsor Inventory'

    def __str__(self):
        return self.title


class SponsorLogo(models.Model):
    name = models.CharField(max_length=120)
    logo = models.ImageField(upload_to='website/sponsors/logos/')
    website_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class SponsorEnquiry(models.Model):
    BUDGET_CHOICES = (
        ('UNDER_1L', 'Under ₹1 Lakh'),
        ('1L_5L', '₹1–5 Lakhs'),
        ('5L_10L', '₹5–10 Lakhs'),
        ('10L_PLUS', '₹10 Lakhs+'),
        ('DISCUSS', 'Open to Discussion'),
    )
    company_name = models.CharField(max_length=180)
    contact_person = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=120)
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    objectives = models.TextField()
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sponsor Enquiry'
        verbose_name_plural = 'Sponsor Enquiries'

    def __str__(self):
        return f'{self.company_name} - {self.get_budget_range_display()}'


class CareerPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Careers At RNTMPL')
    title = models.CharField(max_length=180, default='Build Your Career In Cricket')
    description = models.TextField(default='Join a team working across league operations, media, scoring, technology, partnerships and player experiences.')
    banner_image = models.ImageField(upload_to='website/careers/banner/', blank=True, null=True)
    openings_title = models.CharField(max_length=120, default='Current Opportunities')
    benefits_title = models.CharField(max_length=120, default='Why Work With RNTMPL')
    process_title = models.CharField(max_length=120, default='Our Hiring Process')
    form_title = models.CharField(max_length=120, default='Apply To Join The Team')

    class Meta:
        verbose_name = 'Career Page Settings'
        verbose_name_plural = 'Career Page Settings'

    def __str__(self):
        return 'Career Page Settings'


class AboutPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='About RNTMPL')
    title = models.CharField(max_length=180, default='Building A Clear Pathway For Indian Cricket')
    description = models.TextField(default='RNTMPL connects ambitious players with verified opportunities, structured competition and professional cricket operations.')
    banner_image = models.ImageField(upload_to='website/about/banner/', blank=True, null=True)
    mission_title = models.CharField(max_length=120, default='Our Mission')
    mission_content = models.TextField(default='To create a trusted cricket ecosystem where talent can register, compete, perform and progress through a transparent pathway.')
    vision_title = models.CharField(max_length=120, default='Our Vision')
    vision_content = models.TextField(default='To become India’s most dependable platform for grassroots cricket development, competition and opportunity.')
    values_title = models.CharField(max_length=120, default='What Guides Us')
    founder_eyebrow = models.CharField(max_length=80, default='Founder')
    founder_name = models.CharField(max_length=120, default='RNTMPL Founder')
    founder_designation = models.CharField(max_length=120, default='Founder & Director')
    founder_message = models.TextField(default='RNTMPL was founded with a commitment to give serious cricketers a structured, transparent and professional pathway to compete and progress.')
    founder_image = models.ImageField(upload_to='website/about/founder/', blank=True, null=True)
    founder_linkedin_url = models.URLField(blank=True)
    leadership_title = models.CharField(max_length=120, default='Leadership Team')
    teams_title = models.CharField(max_length=120, default='Teams In The Ecosystem')
    cta_title = models.CharField(max_length=180, default='Ready To Begin Your Cricket Journey?')
    cta_description = models.CharField(max_length=255, default='Create your verified profile and take the next step towards organised competitive cricket.')
    cta_button_text = models.CharField(max_length=60, default='Register As Player')
    cta_button_url = models.CharField(max_length=255, default='/register-player/')

    class Meta:
        verbose_name = 'About Page Settings'
        verbose_name_plural = 'About Page Settings'

    def __str__(self):
        return 'About Page Settings'


class AboutValue(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='icon-check-circle', help_text='Feather icon class, e.g. icon-shield')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title


class AboutLeader(models.Model):
    name = models.CharField(max_length=120)
    designation = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='website/about/leaders/', blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class TeamPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='RNTMPL Teams')
    title = models.CharField(max_length=180, default='Meet The Teams')
    description = models.TextField(default='Explore active teams, squads, leadership and competitive records across the RNTMPL cricket ecosystem.')
    banner_image = models.ImageField(upload_to='website/teams/banner/', blank=True, null=True)
    search_placeholder = models.CharField(max_length=100, default='Search team or city')
    all_categories_text = models.CharField(max_length=50, default='All Categories')
    empty_title = models.CharField(max_length=120, default='No teams found')
    empty_description = models.CharField(max_length=255, default='Team profiles will appear here when they are published.')
    detail_back_text = models.CharField(max_length=40, default='All Teams')
    squad_title = models.CharField(max_length=100, default='Current Squad')
    staff_title = models.CharField(max_length=100, default='Team Staff')
    achievements_title = models.CharField(max_length=100, default='Achievements')

    class Meta:
        verbose_name = 'Team Page Settings'
        verbose_name_plural = 'Team Page Settings'

    def __str__(self):
        return 'Team Page Settings'


class JobOpening(models.Model):
    EMPLOYMENT_CHOICES = (
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
        ('FREELANCE', 'Freelance'),
    )
    title = models.CharField(max_length=160)
    department = models.CharField(max_length=120)
    location = models.CharField(max_length=120, default='India')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES)
    summary = models.TextField()
    requirements = models.TextField(help_text='Enter one requirement per line.')
    application_deadline = models.DateField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    job = models.ForeignKey(JobOpening, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    city = models.CharField(max_length=100)
    experience_years = models.PositiveSmallIntegerField(default=0)
    current_role = models.CharField(max_length=160, blank=True)
    linkedin_url = models.URLField(blank=True)
    resume = models.FileField(upload_to='website/careers/resumes/')
    cover_note = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.job or "General Application"}'


class PartnerEnquiry(models.Model):
    PARTNER_TYPE_CHOICES = (
        ('SPONSOR', 'Sponsor'),
        ('ACADEMY', 'Cricket Academy'),
        ('VENUE', 'Venue Partner'),
        ('MEDIA', 'Media Partner'),
        ('TECHNOLOGY', 'Technology Partner'),
        ('COMMUNITY', 'Community Partner'),
        ('OTHER', 'Other'),
    )
    organisation_name = models.CharField(max_length=180)
    contact_person = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPE_CHOICES)
    website = models.URLField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Partner Enquiry'
        verbose_name_plural = 'Partner Enquiries'

    def __str__(self):
        return f'{self.organisation_name} - {self.get_partner_type_display()}'


class PublicContentPage(models.Model):
    PAGE_CHOICES = (
        ('privacy-policy', 'Privacy Policy'),
        ('terms-conditions', 'Terms & Conditions'),
        ('refund-policy', 'Refund & Cancellation Policy'),
        ('disclaimer', 'Disclaimer'),
    )
    page_type = models.CharField(max_length=40, choices=PAGE_CHOICES, unique=True)
    eyebrow = models.CharField(max_length=80, default='RNTMPL Information')
    title = models.CharField(max_length=180)
    summary = models.TextField(blank=True)
    content = models.TextField(help_text='Use plain text. Separate sections with blank lines.')
    banner_image = models.ImageField(upload_to='website/legal/banner/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['page_type']
        verbose_name = 'Public Policy Page'
        verbose_name_plural = 'Public Policy Pages'

    def __str__(self):
        return self.get_page_type_display()


class FAQPageSettings(models.Model):
    eyebrow = models.CharField(max_length=80, default='Help Centre')
    title = models.CharField(max_length=180, default='Frequently Asked Questions')
    description = models.TextField(default='Find clear answers about registration, trials, teams, events, payments and the RNTMPL platform.')
    banner_image = models.ImageField(upload_to='website/faq/banner/', blank=True, null=True)
    contact_title = models.CharField(max_length=160, default='Still Need Help?')
    contact_description = models.CharField(max_length=255, default='Our support team can help with registration, trials, payments and platform questions.')

    class Meta:
        verbose_name = 'FAQ Page Settings'
        verbose_name_plural = 'FAQ Page Settings'

    def __str__(self):
        return 'FAQ Page Settings'


class PublicFAQ(models.Model):
    CATEGORY_CHOICES = (
        ('REGISTRATION', 'Registration'),
        ('TRIALS', 'Trials & Selection'),
        ('PAYMENTS', 'Payments'),
        ('TEAMS', 'Teams & Events'),
        ('ACCOUNT', 'Account & Support'),
        ('GENERAL', 'General'),
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Public FAQ'
        verbose_name_plural = 'Public FAQs'

    def __str__(self):
        return self.question


class PlayerRegistrationApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACCOUNT_PENDING = 'ACCOUNT_PENDING', 'Account Verification Pending'
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
        PAYMENT_SUBMITTED = 'PAYMENT_SUBMITTED', 'Payment Submitted'
        COMPLETED = 'COMPLETED', 'Completed'

    class PaymentStatus(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        PENDING = 'PENDING', 'Payment Pending'
        SUBMITTED = 'SUBMITTED', 'Verification Pending'
        VERIFIED = 'VERIFIED', 'Payment Verified'
        REJECTED = 'REJECTED', 'Payment Rejected'

    class TrialStatus(models.TextChoices):
        LOCKED = 'LOCKED', 'Complete Payment First'
        ELIGIBLE = 'ELIGIBLE', 'Eligible for Trial'
        INVITED = 'INVITED', 'Invited'
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        ATTENDED = 'ATTENDED', 'Attended'
        SELECTED = 'SELECTED', 'Selected'
        REJECTED = 'REJECTED', 'Not Selected'
        WAITLISTED = 'WAITLISTED', 'Waitlisted'

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, null=True, blank=True, related_name='player_registration')
    player = models.OneToOneField('players.PlayerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='registration_application')
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, blank=True)
    batting_style = models.CharField(max_length=20, blank=True)
    bowling_style = models.CharField(max_length=30, blank=True)
    is_wicket_keeper = models.BooleanField(default=False)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    playing_experience = models.PositiveSmallIntegerField(default=0)
    academy_or_club = models.CharField(max_length=180, blank=True)
    highest_level = models.CharField(max_length=80, blank=True)
    achievements = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=120, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_STARTED,
        db_index=True,
    )
    trial_status = models.CharField(
        max_length=20,
        choices=TrialStatus.choices,
        default=TrialStatus.LOCKED,
        db_index=True,
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT, db_index=True)
    consent_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Player Registration Application'
        verbose_name_plural = 'Player Registration Applications'

    def __str__(self):
        return f'{self.full_name} - {self.get_status_display()}'


class PlayerPaymentTransaction(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
        FAILED = 'FAILED', 'Failed'

    class Provider(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        RAZORPAY = 'RAZORPAY', 'Razorpay'

    application = models.ForeignKey(
        PlayerRegistrationApplication,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='player_payments',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=120, unique=True, db_index=True)
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.MANUAL,
        db_index=True,
    )
    gateway_order_id = models.CharField(max_length=120, blank=True, db_index=True)
    gateway_payment_id = models.CharField(max_length=120, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_player_payments',
    )
    review_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.reference} - {self.get_status_display()}'


class PlayerTrialEvent(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        related_name='player_trials',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_player_trials',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return f'{self.title} - {self.tenant.name}'


class PlayerTrialInvitation(models.Model):
    application = models.ForeignKey(
        PlayerRegistrationApplication,
        on_delete=models.CASCADE,
        related_name='trial_invitations',
    )
    trial = models.ForeignKey(
        PlayerTrialEvent,
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    status = models.CharField(
        max_length=20,
        choices=PlayerRegistrationApplication.TrialStatus.choices,
        default=PlayerRegistrationApplication.TrialStatus.INVITED,
        db_index=True,
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    attended_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['application', 'trial'],
                name='unique_player_application_trial',
            )
        ]
        ordering = ['-invited_at']

    def __str__(self):
        return f'{self.application.full_name} - {self.trial.title}'


class PlayerTrialEvaluation(models.Model):
    class Recommendation(models.TextChoices):
        SELECT = 'SELECT', 'Select'
        REJECT = 'REJECT', 'Reject'
        WAITLIST = 'WAITLIST', 'Waitlist'

    invitation = models.OneToOneField(
        PlayerTrialInvitation,
        on_delete=models.CASCADE,
        related_name='evaluation',
    )
    batting_score = models.PositiveSmallIntegerField(default=0)
    bowling_score = models.PositiveSmallIntegerField(default=0)
    fielding_score = models.PositiveSmallIntegerField(default=0)
    fitness_score = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    recommendation = models.CharField(
        max_length=20, choices=Recommendation.choices
    )
    evaluated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='player_trial_evaluations',
    )
    evaluated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Evaluation: {self.invitation}'


class ContactSubmission(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=180)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.subject}'
