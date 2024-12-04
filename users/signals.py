from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from users.models import User, UserIngreList
from django.db.models.signals import post_save

@receiver(email_confirmed)
def activate_user(sender, request, email_address, **kwargs):
    """
    이메일 인증 완료 후 계정을 활성화합니다.
    """
    user = email_address.user  # 인증된 사용자 가져오기
    user.is_active = True  # 계정 활성화
    user.save()

@receiver(post_save, sender=UserIngreList)
def update_priority_on_save(sender, instance, **kwargs):
    """
    UserIngreList가 저장될 때 자동으로 우선순위를 재계산합니다.
    """
    instance.calculate_priority()

@receiver(post_save, sender=UserIngreList)
def update_priority_on_save(sender, instance, created, **kwargs):
    """
    UserIngreList가 저장될 때 우선순위를 계산합니다.
    """
    if created or instance.priority is None:
        instance.calculate_priority()
        # 우선순위가 업데이트되었으므로 save 대신 update 사용
        UserIngreList.objects.filter(pk=instance.pk).update(priority=instance.priority)
