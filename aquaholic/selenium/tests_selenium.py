from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from django.contrib.auth.models import User
from seleniumlogin import force_login


class AuthenticatedViewTests(StaticLiveServerTestCase):
    fixtures = ['data/users.json', 'data/aquaholic.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='myuser', password='password')
        force_login(self.user, self.selenium, self.live_server_url)

    def test_authenticated_user_can_calculate_correctly(self):
        """Explore calculate page for authenticated user.

        User can calculate the amount of water that they should drink per day
        by inputting weight and exercise duration and click 'calculate' button.
        """
        path = f"aquaholic/{self.user.id}/calculate"
        self.selenium.get(('{}/' + path).format(self.live_server_url))
        weight_input = self.selenium.find_element(By.NAME, "weight")
        weight_input.send_keys(50)
        exercise_duration_input = self.selenium.find_element(By.NAME, "exercise_duration")
        exercise_duration_input.send_keys(60)
        self.selenium.find_element(By.XPATH, "/html/body/div[2]/div/div[1]/form/button").click()
        result = self.selenium.find_element(By.ID, "amount-result")
        self.assertIn("2339.73", result.text)
