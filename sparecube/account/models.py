from __future__ import unicode_literals

from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager, UserManager
)
from django.utils.translation import gettext_lazy as _

from utils import crypt as c


# Class that defines the create_user and createsuperuser methods:
class UserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        # create and saves a USer with the fiven email and password
        if not email:
            #raise ValueError('Email is Required')
            email = c.randEmail()

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        extra_fields.setdefault('is_active', True) # active account
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            #raise ValueError('Email is Required')
            email = c.randEmail()

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password=password, **extra_fields)
    

# Our custom user model
class Utente(AbstractBaseUser, PermissionsMixin):

    id_azienda = models.IntegerField(_('id_azienda'), blank=False, default=0)

    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    username = models.CharField(_('username'), max_length=150, help_text=_('Obbligatorio. 150 caratteri o meno. Lettere, digiti e _ solamente.'), blank=True)
    
    email = models.EmailField(_('email'), max_length=80, unique=True, help_text=_('Obbligatorio. 150 caratteri o meno. Lettere, digiti e _ solamente.'), error_messages={'Errors': _("Email non disponibile."),})

    account_type = models.CharField(_('account_type'), blank=True, max_length=5)

    # se é account attivo
    is_active = models.BooleanField(_('is_active'), blank=False, default=True) #use this to activate accounts
    # se é staff
    is_staff = models.BooleanField(_('is_staff'), blank=False, default=False) # use this to identify if the account is for operators or not


    objects = UserManager()

    # Field for login / for unique identifier
    USERNAME_FIELD = 'email'

    # Field for command createsuperuser
    REQUIRED_FIELDS = ['first_name', 'last_name', 'account_type'] #all the required field except username and password to create a super account


    def __str__(self) -> str:
        return f"{self.email}"
    
    def save(self, *args, **kwargs):
        super(Utente, self).save(*args, **kwargs)
        return self