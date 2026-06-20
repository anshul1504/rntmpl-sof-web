"""
Tenant-aware model managers and querysets for the Cricket Ecosystem Platform.
Every tenant-owned table must use TenantScopedManager or TenantScopedQueryset.
"""
from django.db import models
from django.db.models import Q


class ActiveQueryset(models.QuerySet):
    """Filters out soft-deleted records by default."""

    def delete(self):
        return self.update(is_deleted=True, deleted_at=models.functions.Now())

    def hard_delete(self):
        return super().delete()


class ActiveManager(models.Manager):
    """Manager that excludes soft-deleted records."""

    def get_queryset(self):
        return ActiveQueryset(self.model, using=self._db).filter(is_deleted=False)

    def include_deleted(self):
        return ActiveQueryset(self.model, using=self._db)

    def only_deleted(self):
        return ActiveQueryset(self.model, using=self._db).filter(is_deleted=True)


class TenantScopedQueryset(ActiveQueryset):
    """Queryset that enforces tenant isolation on every query."""

    def for_tenant(self, tenant):
        """Filter to records belonging to a specific tenant."""
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)

    def for_tenant_or_global(self, tenant):
        """Filter to tenant records or global records (tenant__isnull=True)."""
        if tenant is None:
            return self.none()
        return self.filter(Q(tenant=tenant) | Q(tenant__isnull=True))


class TenantScopedManager(ActiveManager):
    """Manager that requires a tenant to be passed explicitly."""

    def get_queryset(self):
        return TenantScopedQueryset(self.model, using=self._db)

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)

    def for_tenant_or_global(self, tenant):
        return self.get_queryset().for_tenant_or_global(tenant)
