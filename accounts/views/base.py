from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import (ListView, DetailView, UpdateView, DeleteView,
        FormView)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404

from accounts.models import Account, AccountUser
from accounts.views.mixins import (AccountAuthMixin, AccountSingleObjectMixin,
        AccountUserSingleObjectMixin, AccountsUpdateMixin)

from accounts.forms import (AccountUserForm, AccountUserAddForm,
        AccountAddForm, ProfileUserForm)


class BaseAccountList(AccountAuthMixin, ListView):
    """
    List all documents for all clients

    Filter by category, client
    """
    model = Account
    context_object_name = "accounts"


class BaseAccountDetail(AccountSingleObjectMixin, DetailView):
    """
    View to show information about a document, contingent on the user having
    access to the document.

    Also provides base view fucntionality to the file view.
    """
    def get_context_data(self, **kwargs):
        context = super(BaseAccountDetail, self).get_context_data(**kwargs)
        context['accountusers'] = self.object.users.all()
        context['account'] = self.object
        return context


class BaseAccountCreate(AccountAuthMixin, FormView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    form_class = AccountAddForm
    template_name = 'accounts/account_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = form.save()
        return super(BaseAccountCreate, self).form_valid(form)


class BaseAccountUpdate(AccountsUpdateMixin, AccountSingleObjectMixin, UpdateView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    pass


class BaseAccountDelete(AccountSingleObjectMixin, DeleteView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    def get_success_url(self):
        return reverse("account_list")


class BaseAccountUserList(AccountSingleObjectMixin, ListView):
    """
    List all users for a given account
    """
    def get(self, request, *args, **kwargs):
        self.account = self.get_account(**kwargs)
        self.object_list = self.account.users.all()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(accountusers=self.object_list,
                account=self.account)
        return self.render_to_response(context)


class BaseAccountUserDetail(AccountUserSingleObjectMixin, DetailView):
    """
    View to show information about a document, contingent on the user having
    access to the document.

    Also provides base view fucntionality to the file view.
    """
    pass


class BaseAccountUserCreate(AccountSingleObjectMixin, FormView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    form_class = AccountUserAddForm
    template_name = 'accounts/accountuser_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        """
        Create the User object, then the AccountUser object, then return the
        user to the account page
        """
        form.save(self.object)
        return super(BaseAccountUserCreate, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(**kwargs)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form,
            account=self.object))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object(**kwargs)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class BaseAccountUserUpdate(AccountsUpdateMixin, AccountUserSingleObjectMixin,
        UpdateView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    form_class = AccountUserForm


class BaseAccountUserDelete(AccountUserSingleObjectMixin, DeleteView):
    """
    This is a view restricted to providers. The data displayed in the form and
    the data pulled back in the from must correspond to the user's provider
    account.
    """
    def get_success_url(self):
        return reverse("accountuser_list")


class UserProfileView(AccountAuthMixin, FormView):
    """
    Profile view that is specific to the logged in user
    """
    form_class = ProfileUserForm
    template_name = "accounts/accountuser_form.html"
    success_url = "/"

    def success_redirect(self, referrer):
        return HttpResponseRedirect(referrer or self.success_url)

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context['profile'] = True
        return context

    def form_valid(self, form):
        """
        Saves updates to the User model
        """
        # Save the user
        self.user.username = form.cleaned_data['username']
        self.user.first_name = form.cleaned_data['first_name']
        self.user.last_name = form.cleaned_data['last_name']
        self.user.email = form.cleaned_data['email']
        if form.cleaned_data['password1']:
            self.user.set_password(form.cleaned_data['password1'])
        self.user.save()
        return self.success_redirect(form.cleaned_data['referrer'])

    def get(self, request, *args, **kwargs):
        self.referrer = request.META.get('HTTP_REFERER')
        self.user = request.user
        form = ProfileUserForm(initial={
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'referrer': self.referrer,})
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.user = request.user
        return super(UserProfileView, self).post(request, *args, **kwargs)