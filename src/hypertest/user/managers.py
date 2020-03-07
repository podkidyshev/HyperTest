from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password, email=None, is_admin=False, is_active=True):
        if email is not None:
            email = self.normalize_email(email)

        user = self.model(username=username, email=email, is_admin=is_admin, is_active=is_active)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, username, password):
        return self.create_user(username, password, is_admin=True)
