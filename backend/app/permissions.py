"""Catalog of every permission the platform knows about.

Roles are data (admins create them in the UI); permissions are code: a role is just a named set of keys from this catalog, and
every protected endpoint names the key it needs. Add a new key here, guard the endpoint with `require_permission(key)`, and the
built-in `admin` role picks it up automatically on the next start.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    key: str
    group: str
    label: str  # shown in the role editor (Persian, like the rest of the UI)


CATALOG: tuple[Permission, ...] = (
    Permission("system.view", "نمای کلی", "مشاهده وضعیت و جزئیات سیستم"),
    Permission("analytics.view", "نمای کلی", "مشاهده آمار و تحلیل‌ها"),
    Permission("documents.manage", "دانش", "مدیریت مستندات (افزودن، ویرایش، حذف، ایندکس)"),
    Permission("skills.manage", "دانش", "مدیریت مهارت‌ها"),
    Permission("lessons.review", "دانش", "بازبینی و تأیید آموزش‌ها"),
    Permission("gaps.view", "دانش", "مشاهده شکاف‌های دانش"),
    Permission("cache.manage", "دانش", "مدیریت کش جستجوی وب"),
    Permission("mcp.manage", "ابزارها و دسترسی", "مدیریت سرورهای MCP"),
    Permission("containers.logs_all", "ابزارها و دسترسی", "مشاهده لاگ و وضعیت همه کانتینرها"),
    Permission("containers.actions_all", "ابزارها و دسترسی", "اجرای start/stop/restart روی همه کانتینرها"),
    Permission("containers.manage_access", "ابزارها و دسترسی", "تعیین دسترسی کانتینرها برای کاربران و مشاهده گزارش عملیات"),
    Permission("conversations.view_all", "گفتگوها", "مشاهده گفتگوهای همه کاربران"),
    Permission("conversations.manage", "گفتگوها", "بازبینی گفتگوها (تغییر وضعیت، ارتقا به سند، رد راه‌حل)"),
    Permission("users.manage", "مدیریت", "مدیریت کاربران و تخصیص نقش"),
    Permission("roles.manage", "مدیریت", "مدیریت نقش‌ها و دسترسی‌ها"),
    Permission("settings.manage", "مدیریت", "تغییر تنظیمات سیستم"),
)

ALL_KEYS: frozenset[str] = frozenset(p.key for p in CATALOG)

ADMIN_ROLE = "admin"  # system role: always holds every permission, cannot be edited or deleted
USER_ROLE = "user"  # system role: assigned to new users by default; permissions editable, role cannot be deleted
