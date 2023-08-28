import logging
import time
from datetime import timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Optional

import selenium.common.exceptions
from attr import define, field
from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from automsr.browser.browser import Browser
from automsr.config import Config, Profile
from automsr.datatypes.dashboard import (
    Dashboard,
    Promotion,
    PromotionType,
    QuizType,
)
from automsr.datatypes.execution import (
    OutcomeType,
    Status,
    Step,
    StepType,
)
from automsr.mail import EmailExecutor
from automsr.search import RandomSearchGenerator

logger = logging.getLogger(__name__)


class ExecutorException(Exception):
    """
    Base class for Executor exceptions.
    """


class QuizException(ExecutorException):
    """
    Base class for Quiz Promotions exceptions.
    """


class CannotFindStartButtonException(QuizException):
    """
    Exception raised when the Start button for quizzes is expected but not found.
    """


class CannotDetermineQuizTypeException(QuizException):
    """
    Exception raised when the Executor is unable to determine
    the quiz-type of a promotion.
    """


@define
class SingleTargetExecutor:
    """
    Executor class driving the completion of all the tasks associated with Rewards.

    This executor will target a single profile.
    """

    config: Config
    profile: Profile
    browser: Browser = field(init=False)

    def _get_execution_function(
        self, step_type: StepType, dashboard: Optional[Dashboard] = None
    ) -> Callable[[], Optional[Dashboard]]:
        """
        Return the function associated to the input execution step.
        """

        func: Callable[[], Optional[Dashboard]]

        if step_type is StepType.START_SESSION:
            return self.start_session

        elif step_type is StepType.GET_DASHBOARD:
            func = self.get_dashboard

        elif step_type in (
            StepType.PROMOTIONS,
            StepType.PUNCHCARDS,
            StepType.PC_SEARCHES,
            StepType.MOBILE_SEARCHES,
        ):
            assert dashboard is not None

            if step_type is StepType.PROMOTIONS:
                func = partial(self.execute_promotions, dashboard=dashboard)
            elif step_type is StepType.PUNCHCARDS:
                func = partial(self.execute_punchcards, dashboard=dashboard)
            elif step_type is StepType.PC_SEARCHES:
                func = partial(self.execute_pc_searches, dashboard=dashboard)
            elif step_type is StepType.MOBILE_SEARCHES:
                func = partial(self.execute_mobile_searches, dashboard=dashboard)
            else:
                raise ValueError(step_type)

        elif step_type is StepType.END_SESSION:
            func = self.end_session

        else:
            raise ValueError(step_type)

        return func

    def execute(self) -> Status:
        """
        Execute the following steps:
        - Open a new browser session with Selenium and a Chrome driver.
        - Retrieval of dashboard json from Rewards page
        - Execution of all completable punchcards
        - Execution of all completable promotions
        - Execution of searches:
            - PC searches (desktop user agent)
            - Mobile searches (mobile user agent)

        Returns the Status of the execution for the current profile.
        """

        # Construct the list of statuses for each step.
        steps: List[Step] = []

        # Get the list of steps in the correct order of execution
        step_types: List[StepType] = StepType.get_ordered_steps()

        # If the profile is marked as skipped, return this result.
        if self.profile.skip:
            logger.info("Profile marked as skipped.")
            steps = [
                Step(type=step_type, outcome=OutcomeType.SKIPPED)
                for step_type in step_types
            ]
            status = Status(
                profile=self.profile,
                steps=steps,
            )
            return status

        # Declare the variables needed in the following loop.
        dashboard: Optional[Dashboard] = None
        for step_type in step_types:
            logger.debug("Step type under execution: %s", step_type)

            # Get the function to use.
            function = self._get_execution_function(
                step_type=step_type, dashboard=dashboard
            )

            # Declare the outcome of the step.
            outcome: Optional[OutcomeType] = None

            # Declare the explanation of the step, if non-success.
            explanation: Optional[str] = None

            # Snapshot a performance counter and returns the value in seconds.
            start_counter: float = time.perf_counter()
            duration: Optional[timedelta] = None

            try:
                # If the step is get-dashboard, we will expect a return value.
                if step_type is StepType.GET_DASHBOARD:
                    dashboard = function()
                    assert isinstance(dashboard, Dashboard)

                # Otherwise, just execute the function.
                else:
                    retval = function()
                    assert retval is None

            # Catch exceptions block.
            # Selenium errors will be treated as normal errors, but won't fail the entire execution;
            #  only the corresponding step will be marked as failed.
            except selenium.common.exceptions.WebDriverException as e:
                outcome = OutcomeType.FAILURE
                explanation = str(e)
                logger.error("Selenium exception caught: %s", e)

            # This is needed for Punchcards.
            except NotImplementedError:
                outcome = OutcomeType.SKIPPED
                explanation = "Step not implemented yet."
                logger.warning(explanation)

            # If no exception is raised, the step is successful.
            # Otherwise, any uncaught exception will be propagated to the caller.
            else:
                outcome = OutcomeType.SUCCESS
                logger.debug("Step completed correctly.")

            # At the end of the try-except block, we will have an outcome, a duration,
            # and possibly an explanation.
            finally:
                # Capture time elapsed.
                end_counter = time.perf_counter()
                seconds = end_counter - start_counter
                duration = timedelta(seconds=seconds)

                # Create step based on step status.
                assert outcome is not None
                step = Step(
                    type=step_type,
                    outcome=outcome,
                    duration=duration,
                    explanation=explanation,
                )

                # Append the created step status to the list of statuses.
                steps.append(step)

        # Create the overall status for the current profile, and return it to the caller.
        status = Status(profile=self.profile, steps=steps)
        return status

    def start_session(self) -> None:
        """
        Create a new session with Selenium and Chromedriver,
        then returns the session object to the caller.
        """

        self.browser = Browser.from_config(config=self.config, profile=self.profile)
        self.browser.test_driver()
        self.browser.go_to(self.config.automsr.rewards_homepage)

        # Simulate the user landing on the page and waiting a little bit
        time.sleep(2)

    def end_session(self) -> None:
        """
        Terminate the session.
        """

        self.browser.driver.quit()

    def get_dashboard(self) -> Dashboard:
        """
        Retrieve a Dashboard object from the current page.

        This method is expected to be run inside the Rewards homepage.
        """

        raw_data: Dict[str, Any] = self.browser.execute_script("return dashboard;")
        dashboard = Dashboard(**raw_data)
        return dashboard

    def execute_pc_searches(self, dashboard: Dashboard) -> None:
        """
        Execute PC searches, if needed.
        """

        if (amount := dashboard.amount_of_pc_searches()) == 0:
            logger.info("No PC search is needed")
            return
        else:
            logger.info("Starting PC searches")

        assert amount > 0
        return self._execute_searches(
            amount=amount, user_agent=self.browser.user_agents.desktop
        )

    def execute_mobile_searches(self, dashboard: Dashboard) -> None:
        """
        Execute Mobile searches, if needed.
        """

        if (amount := dashboard.amount_of_mobile_searches()) == 0:
            logger.info("No Mobile search is needed")
            return
        else:
            logger.info("Starting Mobile searches")

        assert amount > 0
        return self._execute_searches(
            amount=amount, user_agent=self.browser.user_agents.mobile
        )

    def _execute_searches(
        self, amount: int = 1, user_agent: Optional[str] = None
    ) -> None:
        """
        Helper method to execute `amount` searches.

        Can specify a custom `user_agent` to use.
        """

        assert amount >= 1, "Invalid value!"

        safe_amount = amount + 5
        logger.debug("Original amount of searches: %s", amount)
        logger.debug("Safe amount of searches: %s", safe_amount)

        old_user_agent: Optional[str] = None
        if user_agent is not None:
            logger.debug("Changing user-agent to: %s", user_agent)
            old_user_agent = self.browser.get_user_agent()
            self.browser.change_user_agent(user_agent=user_agent)

        search_generator = RandomSearchGenerator()
        sleep_time = search_generator.sleep_time()
        query = search_generator.query_gen()

        self.browser.go_to_bing()

        for i in tqdm(range(safe_amount)):
            logger.debug("Executing search: %s/%s", i + 1, safe_amount)

            # we retrieve the element in the for-loop since the page is reloaded, thus the element can be invalidated
            element: WebElement = self.browser.driver.find_element(
                by=By.ID, value="sb_form_q"
            )

            # send the next item of the generator to the input field
            element.send_keys(next(query))

            # sleep to prevent issues with Selenium interacting with the page
            time.sleep(0.5)

            # send ENTER to perform a search
            element.send_keys(Keys.ENTER)

            # sleep a certain amount of time
            time.sleep(sleep_time)

        if user_agent is not None:
            logger.debug("Restoring original user-agent: %s", old_user_agent)
            assert old_user_agent is not None
            self.browser.change_user_agent(user_agent=old_user_agent)

    def execute_promotions(self, dashboard: Dashboard) -> None:
        """
        Execute all completable promotions.
        """

        # handle promotional items differently, since there is another way
        # to retrieve the corresponding WebElement
        promotional_item = dashboard.get_promotional_item()
        if promotional_item is not None:
            try:
                self.browser.open_promotion(
                    promotion=promotional_item, element_id="promo-item"
                )
            except Exception as e:
                logger.error("Exception caught: %s", e)
                logger.warning("Promotion '%s' will be skipped", promotional_item)
            finally:
                # simulate navigation
                logger.debug("Re-opening Rewards homepage to simulate navigation.")
                self.browser.go_to_rewards()
                logger.debug("Sleeping to simulate a real user behavior.")
                time.sleep(2)

        # handle all other promotions
        promotions: List[Promotion] = dashboard.get_completable_promotions()

        for promotion in promotions:
            logger.info("Executing promotion: %s", promotion.title)
            try:
                self._execute_promotion(promotion=promotion)
            except Exception as e:
                logger.error("Exception caught: %s", e)
                logger.warning("Promotion '%s' will be skipped", promotion)
            finally:
                # simulate navigation
                logger.debug("Re-opening Rewards homepage to simulate navigation.")
                self.browser.go_to_rewards()
                logger.debug("Sleeping to simulate a real user behavior.")
                time.sleep(2)

    def _execute_promotion(self, promotion: Promotion) -> None:
        """
        Execute a specific promotion.
        """

        driver = self.browser.driver
        self.browser.open_promotion(promotion=promotion)

        # Sleep to simulate user behavior and to let JS load the page
        time.sleep(3)

        # Determine which promotion is currently on
        if promotion.promotionType == PromotionType.QUIZ:
            # Try to determine which quiz we are dealing with
            try:
                _ = driver.find_element(by=By.ID, value="btoption0")
            except NoSuchElementException:
                pass
            else:
                return self._execute_quiz_promotion(
                    quiz_type=QuizType.CHOICE_BETWEEN_TWO
                )

            # If the quiz is not a choice-between-two, try with the three-questions-N-answers
            try:
                start_button = driver.find_element(by=By.ID, value="rqStartQuiz")
                # if we find the button, we click it and then wait a little bit for JS
                # to load the answers in the DOM
                start_button.click()
                time.sleep(2)
            except NoSuchElementException as e:
                # if we are here, the quiz can be either already started,
                # or something's broken; in the latter case, we raise an error
                try:
                    driver.find_element(by=By.ID, value="currentQuestionContainer")
                except NoSuchElementException:
                    logger.error(
                        "Cannot find neither the start button, nor the quiz container!"
                    )
                    raise CannotFindStartButtonException() from e
                else:
                    logger.info("Quiz already started.")

            # Check if the quiz is 8-answers
            try:
                _ = driver.find_element(by=By.ID, value="rqAnswerOption7")
            except NoSuchElementException:
                pass
            else:
                return self._execute_quiz_promotion(
                    quiz_type=QuizType.THREE_QUESTIONS_EIGHT_ANSWERS
                )

            # Check if the quiz is 4-answers
            try:
                _ = driver.find_element(by=By.ID, value="rqAnswerOption3")
            except NoSuchElementException as e:
                raise CannotDetermineQuizTypeException() from e
            else:
                return self._execute_quiz_promotion(
                    quiz_type=QuizType.THREE_QUESTIONS_FOUR_ANSWERS
                )

        elif promotion.promotionType in (
            PromotionType.URL_REWARD,
            PromotionType.WELCOME_TOUR,
        ):
            logger.info("Promotion executed by just opening the destination url.")
        else:
            raise ValueError(
                f"Cannot execute promotion with type: {promotion.promotionType}"
            )

    def _execute_quiz_promotion(self, quiz_type: QuizType) -> None:
        """
        Execute a specific promotion that is a quiz with a known type.

        The method assumes that, if a quiz type requires for a Start button to be clicked,
        this is done by the caller.
        """

        driver = self.browser.driver

        logger.info("Resolving promotion as quiz with type: %s", quiz_type)

        if quiz_type is QuizType.CHOICE_BETWEEN_TWO:
            button_id = "btoption0"

            # safety breaks
            loop_break = 5
            loop_counter = 1

            while loop_counter < loop_break:
                button = driver.find_element(by=By.ID, value=button_id)
                _class = button.get_attribute("class")
                is_quiz_completed = _class is not None and "selectedOption" in _class

                if is_quiz_completed:
                    logger.info("Quiz finished")
                    return
                else:
                    button.click()

                    # Wait some seconds to let the page reload
                    time.sleep(1)

                loop_counter += 1

            # if we are here, we didn't finish the quiz
            logger.warning("Quiz not finished!")
            return

        elif quiz_type in (
            QuizType.THREE_QUESTIONS_FOUR_ANSWERS,
            QuizType.THREE_QUESTIONS_EIGHT_ANSWERS,
        ):
            # safety breaks
            loop_break = 100
            loop_counter = 1

            # Create the `max_answer_index` based on the provided quiz type.
            if quiz_type is QuizType.THREE_QUESTIONS_FOUR_ANSWERS:
                max_answer_index = 4
            elif quiz_type is QuizType.THREE_QUESTIONS_EIGHT_ANSWERS:
                max_answer_index = 8
            else:
                raise ValueError(f"Invalid quiz type provided: {quiz_type}")

            current_answer_index = 0

            while loop_counter < loop_break:
                # check if quiz is finished
                try:
                    driver.find_element(by=By.ID, value="quizCompleteContainer")
                except NoSuchElementException:
                    logger.debug("Quiz still in progress.")
                else:
                    logger.info("Quiz finished.")
                    return

                # if not, continue with clicking answers
                answer_id = f"rqAnswerOption{current_answer_index}"
                answer_element = driver.find_element(by=By.ID, value=answer_id)
                answer_element.click()

                # update the answer index
                current_answer_index = (current_answer_index + 1) % max_answer_index

                # update the loop counter
                loop_counter += 1

            # if we are here, we didn't finish the quiz
            logger.warning("Quiz not finished!")
            return
        else:
            raise ValueError(f"Quiz type not supported: {quiz_type}")

    def execute_punchcards(self, dashboard: Dashboard) -> None:
        """
        Execute all completable Punchcards, if any.
        """

        raise NotImplementedError


@define
class MultipleTargetsExecutor:
    """
    Executor class driving the completion of all the tasks associated with Rewards.

    This executor will target multiple profiles automatically.
    """

    config: Config

    def execute(self) -> None:
        """
        Spawn a SingleTargetExecutor for every profile specified in the `config` file.
        """

        statuses: List[Status] = []

        for profile in self.config.automsr.profiles:
            logger.info("Profile under execution: %s", profile)
            executor = SingleTargetExecutor(config=self.config, profile=profile)
            status = executor.execute()
            logger.info("Status of execution for profile %s: %s", profile, status)
            statuses.append(status)

        email_executor = EmailExecutor(config=self.config)
        if email_executor.are_messages_enabled():
            email_executor.send_message(statuses=statuses)
