from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from snacks.models import HomeComment, Review, Snack



class SnackListHomeCommentTests(TestCase):
    def setUp(self):
        self.url = reverse("snacks:list")
        self.user = User.objects.create_user(
            username="commenter",
            password="safe-pass-123",
            first_name="Minh",
        )
        self.other_user = User.objects.create_user(
            username="someoneelse",
            password="safe-pass-456",
            first_name="Lan",
        )

    def test_authenticated_user_can_create_home_comment(self):
        self.client.login(username="commenter", password="safe-pass-123")

        response = self.client.post(
            self.url,
            {
                "action": "create",
                "comment": "Dich vu tot va giao hang nhanh.",
            },
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertTrue(
            HomeComment.objects.filter(
                user=self.user,
                comment="Dich vu tot va giao hang nhanh.",
            ).exists()
        )
        self.assertContains(response, "Dich vu tot va giao hang nhanh.")

    def test_anonymous_user_is_redirected_to_login_when_posting_comment(self):
        response = self.client.post(
            self.url,
            {
                "action": "create",
                "comment": "Thu gui comment",
            },
        )

        self.assertEqual(HomeComment.objects.count(), 0)
        self.assertRedirects(
            response,
            f"{reverse('snacks:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_owner_can_update_home_comment(self):
        home_comment = HomeComment.objects.create(
            user=self.user,
            comment="Noi dung cu",
        )
        self.client.login(username="commenter", password="safe-pass-123")

        response = self.client.post(
            f"{self.url}?edit_comment={home_comment.id}",
            {
                "action": "update",
                "comment_id": home_comment.id,
                "comment": "Noi dung moi",
            },
            follow=True,
        )

        home_comment.refresh_from_db()
        self.assertRedirects(response, self.url)
        self.assertEqual(home_comment.comment, "Noi dung moi")

    def test_owner_can_delete_home_comment(self):
        home_comment = HomeComment.objects.create(
            user=self.user,
            comment="Can xoa",
        )
        self.client.login(username="commenter", password="safe-pass-123")

        response = self.client.post(
            self.url,
            {
                "action": "delete",
                "comment_id": home_comment.id,
            },
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertFalse(HomeComment.objects.filter(pk=home_comment.id).exists())

    def test_user_cannot_delete_other_users_comment(self):
        home_comment = HomeComment.objects.create(
            user=self.other_user,
            comment="Comment cua nguoi khac",
        )
        self.client.login(username="commenter", password="safe-pass-123")

        response = self.client.post(
            self.url,
            {
                "action": "delete",
                "comment_id": home_comment.id,
            },
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertTrue(HomeComment.objects.filter(pk=home_comment.id).exists())

    def test_user_cannot_update_other_users_comment(self):
        home_comment = HomeComment.objects.create(
            user=self.other_user,
            comment="Noi dung cua nguoi khac",
        )
        self.client.login(username="commenter", password="safe-pass-123")

        response = self.client.post(
            self.url,
            {
                "action": "update",
                "comment_id": home_comment.id,
                "comment": "Thu sua trai phep",
            },
            follow=True,
        )

        home_comment.refresh_from_db()
        self.assertRedirects(response, self.url)
        self.assertEqual(home_comment.comment, "Noi dung cua nguoi khac")


class SnackDetailReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reviewer",
            password="safe-pass-123",
        )
        self.snack = Snack.objects.create(
            title="Banh trang test",
            author="Snackstore",
            description="Mon an vat test",
            price=25000,
            stock=10,
        )
        self.url = reverse("snacks:detail", kwargs={"slug": self.snack.slug})

    def test_authenticated_user_can_create_product_review(self):
        self.client.login(username="reviewer", password="safe-pass-123")

        response = self.client.post(
            self.url,
            {
                "rating": 5,
                "comment": "San pham ngon va dong goi can than.",
            },
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertTrue(
            Review.objects.filter(
                user=self.user,
                snack=self.snack,
                rating=5,
                comment="San pham ngon va dong goi can than.",
            ).exists()
        )
        self.assertContains(response, "San pham ngon va dong goi can than.")

    def test_anonymous_user_is_redirected_to_login_when_posting_review(self):
        response = self.client.post(
            self.url,
            {
                "rating": 4,
                "comment": "Thu gui danh gia",
            },
        )

        self.assertEqual(Review.objects.count(), 0)
        self.assertRedirects(
            response,
            f"/login/?next={self.url}",
            fetch_redirect_response=False,
        )


# Create your tests here.
