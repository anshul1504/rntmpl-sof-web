from django.contrib import admin
from django.apps import apps

from apps.publicsite import admin as publicsite_admin  # noqa: F401


class WebsiteCMSAdminSite(admin.AdminSite):
    site_header = 'RNTMPL Website CMS'
    site_title = 'Website CMS'
    index_title = 'Manage Public Website'
    enable_nav_sidebar = True
    index_template = 'admin/website_cms_index.html'
    site_url = '/'

    def get_app_list(self, request, app_label=None):
        groups = [
            ('website_setup', 'Website Setup', ('websitesettings',)),
            ('page_management', 'Page Management', (
                'homepage', 'aboutpagesettings', 'teampagesettings',
                'gallerypagesettings', 'blogsettings', 'newspagesettings',
                'contactpagesettings', 'eventpagesettings',
                'partnerpagesettings', 'sponsorpagesettings',
                'careerpagesettings', 'faqpagesettings',
            )),
            ('homepage_content', 'Homepage Content', ('heroslide', 'websitefeature', 'testimonial')),
            ('publishing', 'Publishing', (
                'newspost', 'galleryitem', 'partnerlogo', 'partneropportunity',
                'partnerfaq', 'sponsorlogo', 'sponsorpackage', 'sponsorinventory',
            )),
            ('about_content', 'About Page Content', ('aboutvalue', 'aboutleader')),
            ('careers', 'Careers', ('jobopening', 'jobapplication')),
            ('forms', 'Forms & Enquiries', ('playerregistrationapplication', 'contactsubmission', 'partnerenquiry', 'sponsorenquiry')),
            ('help_legal', 'Help & Legal', ('publicfaq', 'publiccontentpage', 'contactfaq')),
        ]
        available = {}
        for model, model_admin in self._registry.items():
            perms = model_admin.get_model_perms(request)
            if not any(perms.values()):
                continue
            name = model._meta.model_name
            available[name] = {
                'model': model,
                'name': model._meta.verbose_name_plural.title(),
                'object_name': model._meta.object_name,
                'perms': perms,
                'admin_url': f'/website-admin/publicsite/{name}/' if perms.get('view') or perms.get('change') else None,
                'add_url': f'/website-admin/publicsite/{name}/add/' if perms.get('add') else None,
                'view_only': perms.get('view') and not perms.get('change'),
            }
        app_list = []
        for key, title, model_names in groups:
            items = [available[name] for name in model_names if name in available]
            if items:
                app_list.append({
                    'name': title,
                    'app_label': key,
                    'app_url': '#',
                    'has_module_perms': True,
                    'models': items,
                })
        return app_list

    def each_context(self, request):
        context = super().each_context(request)
        context['cms_modules'] = [
            {
                'title': 'Website Setup',
                'description': 'Brand, contact, SEO and global website settings.',
                'icon': 'fas fa-cog',
                'models': ('websitesettings',),
            },
            {
                'title': 'Page Management',
                'description': 'Manage every public page heading, banner and section content.',
                'icon': 'fas fa-file-alt',
                'models': (
                    'homepage', 'aboutpagesettings', 'teampagesettings',
                    'gallerypagesettings', 'blogsettings', 'newspagesettings',
                    'contactpagesettings', 'eventpagesettings',
                    'partnerpagesettings', 'sponsorpagesettings',
                    'careerpagesettings', 'faqpagesettings',
                ),
            },
            {
                'title': 'Homepage Content',
                'description': 'Hero slider, pathway cards, testimonials and homepage sections.',
                'icon': 'fas fa-home',
                'models': ('heroslide', 'websitefeature', 'testimonial'),
            },
            {
                'title': 'Publishing',
                'description': 'Blogs, news, gallery images, partner and sponsor content.',
                'icon': 'fas fa-newspaper',
                'models': (
                    'newspost', 'galleryitem', 'partnerlogo',
                    'partneropportunity', 'partnerfaq', 'sponsorlogo',
                    'sponsorpackage', 'sponsorinventory',
                ),
            },
            {
                'title': 'About Page Content',
                'description': 'Values, leadership and supporting About page records.',
                'icon': 'fas fa-users',
                'models': ('aboutvalue', 'aboutleader'),
            },
            {
                'title': 'Careers',
                'description': 'Job openings and received job applications.',
                'icon': 'fas fa-briefcase',
                'models': ('jobopening', 'jobapplication'),
            },
            {
                'title': 'Forms & Enquiries',
                'description': 'Submitted public forms kept separate from website content.',
                'icon': 'fas fa-inbox',
                'models': ('contactsubmission', 'partnerenquiry', 'sponsorenquiry'),
            },
            {
                'title': 'Help & Legal',
                'description': 'FAQs, privacy, terms, refund policy and disclaimer.',
                'icon': 'fas fa-shield-alt',
                'models': ('publicfaq', 'publiccontentpage', 'contactfaq'),
            },
        ]
        registry = {
            model._meta.model_name: {
                'name': model._meta.verbose_name_plural.title(),
                'url': f'/website-admin/publicsite/{model._meta.model_name}/',
                'add_url': f'/website-admin/publicsite/{model._meta.model_name}/add/',
                'can_add': model_admin.has_add_permission(request),
            }
            for model, model_admin in self._registry.items()
        }
        for module in context['cms_modules']:
            module['items'] = [registry[name] for name in module['models'] if name in registry]
        return context


website_cms_site = WebsiteCMSAdminSite(name='website_cms')

for model, model_admin in list(admin.site._registry.items()):
    if model._meta.app_label == 'publicsite':
        website_cms_site.register(model, model_admin.__class__)
