from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User 
from .models import Booking, Client, Case, Document, Visitor, Availability, LawyerProfile, Message
from .forms import ClientRegistrationForm, ClientProfileForm, CaseForm, DocumentForm, VisitorForm, AppointmentForm, AvailabilityForm
from .decorators import group_required


def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = VisitorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully! We will get back to you shortly.')
            return redirect('landing_page')
    else:
        form = VisitorForm()
    return render(request, 'landing.html', {'form': form})

def register(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False  # Require admin validation
                    user.save()
                    # Create the client profile
                    if not hasattr(user, 'client_profile'):
                        Client.objects.create(
                            user=user,
                            name=form.cleaned_data['name'],
                            email=form.cleaned_data['email']
                        )
                    from django.contrib.auth.models import Group
                    clients_group, created = Group.objects.get_or_create(name='Clients')
                    user.groups.add(clients_group)
                    messages.success(request, 'Your account has been created and is pending admin approval. You will be able to log in once an admin activates your account.')
                    return redirect('login')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Error during registration")
                messages.error(request, 'An unexpected error occurred during registration. Please try again or contact support.')
        return render(request, 'registration/register.html', {'form': form})
    else:
        form = ClientRegistrationForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'title': 'Client Registration'
    })

class ClientProfileView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientProfileForm
    template_name = 'profile.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        """Return Client profile for the logged-in user, creating one if missing."""
        user = self.request.user
        try:
            return user.client_profile
        except Client.DoesNotExist:
            # Create a minimal client profile on first access
            name = (user.get_full_name() or user.username or user.email.split('@')[0]).strip()
            if not user.email:
                # Ensure an email value (use placeholder)
                user.email = f"{user.username}@example.com"
                user.save(update_fields=["email"])
            client = Client.objects.create(
                user=user,
                name=name,
                email=user.email,
            )
            return client

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

def dashboard(request):
    query = request.GET.get('q')
    # If user is admin or lawyer, show all cases/clients
    if request.user.is_superuser or request.user.groups.filter(name__in=['Admin', 'Lawyer']).exists():
        cases = Case.objects.order_by('-opened_on')
        clients = Client.objects.order_by('name')
        if query:
            cases = cases.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(client__name__icontains=query)
            ).distinct()
            clients = clients.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query)
            ).distinct()
    else:
        # If user is a client, only show their own cases and profile
        try:
            client = request.user.client_profile
            cases = Case.objects.filter(client=client).order_by('-opened_on')
            clients = Client.objects.filter(pk=client.pk)
            if query:
                cases = cases.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query)
                ).distinct()
        except Client.DoesNotExist:
            cases = Case.objects.none()
            clients = Client.objects.none()
    context = {
        'cases': cases,
        'clients': clients,
    }
    return render(request, 'dashboard.html', context)

@login_required
@group_required('Admin', 'Lawyer')
def client_create(request):
    if request.method == 'POST':
        form = ClientProfileForm(request.POST)
        if form.is_valid():
            try:
                client = form.save()
                messages.success(request, f'Client "{client.name}" has been created successfully.')
                return redirect('dashboard')
            except Exception as e:
                if 'email' in str(e):
                    messages.error(request, 'A client with this email already exists. Please use a different email address.')
                else:
                    messages.error(request, f'An error occurred: {str(e)}')
    else:
        form = ClientProfileForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add New Client'})

@login_required
@group_required('Admin', 'Lawyer')
def case_create(request):
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save()
            messages.success(request, f'Case "{case.title}" has been created successfully.')
            return redirect('dashboard')
    else:
        form = CaseForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add New Case'})

@login_required
def case_detail(request, pk):
    case = get_object_or_404(Case, pk=pk)
    # Only allow access if admin/lawyer or the client owns the case
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Admin', 'Lawyer']).exists() or (hasattr(request.user, 'client_profile') and case.client == request.user.client_profile)):
        messages.error(request, 'You do not have permission to view this case.')
        return redirect('dashboard')
    documents = Document.objects.filter(case=case)
    form = DocumentForm() # Initialize form for GET request

    if request.method == 'POST':
        # Ensure only authorized users can upload
        if request.user.is_superuser or request.user.groups.filter(name__in=['Admin', 'Lawyer']).exists():
            form = DocumentForm(request.POST, request.FILES)
            if form.is_valid():
                document = form.save(commit=False)
                document.case = case
                document.save()
                messages.success(request, f'Document "{document.title}" has been uploaded successfully.')
                return redirect('case_detail', pk=case.pk)
    
    context = {
        'case': case,
        'documents': documents,
        'form': form,
    }
    return render(request, 'case_detail.html', context)

# def chat_room(request):
#     if request.method == 'POST':
#         message = request.POST.get('message')

#         if message:
#             Message.objects.create(
#                 sender=request.user.username,
#                 content=message
#             )
#             async_to_sync(channel_layer.group_send)(
#                 'chat_group',
#                 {
#                     'type': 'message_received',
#                     'message': message
#                 },
#             )
#             return JsonResponse({'message': 'Message sent successfully!!!'})
        
#     return JsonResponse({'message': 'Invalid request!!!'}, status=400)
#     return render(request, "chat_room.html", {"chat": chat})


@login_required

def chat_room(request, lawyer_id):
    history = Message.objects.filter(lawyer_id=lawyer_id).select_related('sender')
    return render(request, 'chat/chat_room.html', {
        'lawyer_id': lawyer_id,
        'history': history,
    })

    return render(request, 'chat/chat_room.html', {...})

# def chat_room(request, lawyer_id=None):
#     """
#     Renders the chat room template for a given lawyer-client room.
#     The room_name can be constructed as needed (e.g., f"lawyer_{lawyer_id}_client_{request.user.id}")
#     """
#     # You can customize room_name logic as needed for your app
#     if lawyer_id:
#         room_name = f"lawyer_{lawyer_id}_client_{request.user.id}"
#     else:
#         room_name = "lawyer_client_room"
#     return render(request, "chat_room.html", {"room_name": room_name})


def lawyers_list(request):
    # LawyerProfile = get_user_model()
    from .models import LawyerProfile
    lawyers = LawyerProfile.objects.all()
    print(lawyers)
    # Prefetch LawyerProfile for efficiency
    # lawyer_profiles = LawyerProfile.objects.filter(user__in=lawyers)
    # profiles_by_user = {profile.user_id: profile for profile in lawyer_profiles}
    # Attach profile to each lawyer (if exists)
    # for lawyer in lawyers:
    #     lawyer.lawyer_profile_obj = profiles_by_user.get(lawyer.id)
    return render(request, 'lawyers_list.html', {'lawyers': lawyers})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Only allow access if admin/lawyer or the client is viewing their own profile
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Admin', 'Lawyer']).exists() or (hasattr(request.user, 'client_profile') and request.user.client_profile.pk == client.pk)):
        messages.error(request, 'You do not have permission to view this client.')
        return redirect('dashboard')
    cases = Case.objects.filter(client=client)
    context = {
        'client': client,
        'cases': cases
    }
    return render(request, 'client_detail.html', context)

@login_required
@group_required('Admin', 'Lawyer')
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientProfileForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.name}" has been updated successfully.')
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientProfileForm(instance=client)
    return render(request, 'form_template.html', {'form': form, 'title': 'Edit Client'})

@login_required
@group_required('Admin', 'Lawyer')
def case_update(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, f'Case "{case.title}" has been updated successfully.')
            return redirect('case_detail', pk=case.pk)
    else:
        form = CaseForm(instance=case)
    return render(request, 'form_template.html', {'form': form, 'title': 'Edit Case'})

@login_required
def book_appointment(request):
    # Only allow clients to book appointments
    if not hasattr(request.user, 'client_profile'):
        messages.error(request, 'Only clients can book appointments.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user.client_profile
            appointment.save()
            messages.success(request, 'Your appointment has been booked!')
            return redirect('dashboard')
    else:
        form = AppointmentForm()
    return render(request, 'book_appointment.html', {'form': form})


@login_required
def set_availability(request):
    lawyer_profile = LawyerProfile.objects.get(user=request.user)  # current lawyer
    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.lawyer = lawyer_profile
            lawyer_id = request.POST.get("lawyer")
            availability.lawyer = request.user.lawyer_profile  # assign the Lawyer object, not a string
            availability.save()
            return redirect("my_availability")
    else:
        form = AvailabilityForm()

    return render(request, "availability/set_availability.html", {"form": form})


@login_required
def my_availability(request):
    lawyer_profile = LawyerProfile.objects.get(user=request.user)
    slots = Availability.objects.filter(lawyer=lawyer_profile)
    return render(request, "availability/my_availability.html", {"slots": slots})

@login_required
def lawyer_availability(request, user_id):
    lawyer = get_object_or_404(LawyerProfile, user_id=user_id)
    availabilities = Availability.objects.filter(lawyer=lawyer).order_by('day', 'start_time')

        # Annotate each slot with is_booked = True if there is any pending or approved booking
    for slot in availabilities:
        slot.is_booked = slot.bookings.filter(status__in=['pending', 'approved']).exists()

    return render(request, "availability/lawyer_availability.html", {
        "lawyer": lawyer,
        "availabilities": availabilities
    })

@login_required
def book_slot(request, availability_id):
    availability = get_object_or_404(Availability, id=availability_id)

    # Only consider pending or approved bookings as blocking the slot
    if availability.bookings.filter(status__in=['pending', 'approved']).exists():
        return redirect("lawyer_availability", user_id=availability.lawyer.user_id)

    # Create booking
    Booking.objects.create(
        availability=availability,
        client=request.user
    )
    return redirect("lawyer_availability", user_id=availability.lawyer.user_id)

@login_required
def my_bookings(request):
    bookings = request.user.bookings.select_related("availability__lawyer").order_by("-booked_at")
    return render(request, "booking/my_bookings.html", {"bookings": bookings})

@login_required
def lawyer_bookings(request):
    # Find the lawyer profile of the logged-in user
    lawyer = get_object_or_404(LawyerProfile, user=request.user)

    # Get all bookings for this lawyer's availabilities
    bookings = Booking.objects.filter(
        availability__lawyer=lawyer
    ).select_related("availability__lawyer", "client").order_by("-booked_at")

    return render(request, "booking/lawyer_bookings.html", {"bookings": bookings})

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, id=booking_id, availability__lawyer__user=request.user)

    if status in ["approved", "declined"]:
        booking.status = status
        booking.save()

    return redirect("lawyer_bookings")