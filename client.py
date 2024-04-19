import requests
import json
from datetime import datetime

BASE_URL = "https://newssites.pythonanywhere.com/api/"


class Client:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        self.news_service_url = None

    def login(self, command):
        try:
            url = command.split()[1]
        except:
            print("Invalid URL provided.")
            return
        if url == "local":
            url = "http://localhost:8000/"
        if not url or not isinstance(url, str) or "http" not in url:
            raise ValueError("Invalid URL provided.")

        self.news_service_url = url
        username = input("Enter username: ")
        password = input("Enter password: ")

        if not username or not password:
            print("Username and password cannot be empty.")
            return

        payload = {
            "username": username,
            "password": password
        }
        try:
            response = self.session.post(self.news_service_url + "api/login", data=payload)
            response.raise_for_status()
            self.logged_in = True
            print("Logged in successfully.")
            print("Session cookies:", self.session.cookies)
        except requests.RequestException as e:
            print("Failed to log in:", str(e))

    def logout(self):
        if self.logged_in:
            self.logged_in = False
            self.session.close()
            print("Logged out successfully.")

    def input_with_prompt(self, prompt):
        user_input = input(prompt)
        while not user_input.strip():
            print("Input cannot be empty. Please try again.")
            user_input = input(prompt)
        return user_input

    def post_story(self):
        if not self.logged_in:
            print("Please login first.")
            return

        headline = self.input_with_prompt("Enter headline: ")
        if len(headline) > 64:
            print("Headline must be 64 characters or less.")
            return
        category = self.input_with_prompt("Enter category: {pol, art, tech, trivia} ")
        if category not in {'pol', 'art', 'tech', 'trivia'}:
            print("Invalid category.")
            return
        region = self.input_with_prompt("Enter region: {uk, eu, w} ")
        if region not in {'uk', 'eu', 'w'}:
            print("Invalid region.")
            return
        details = self.input_with_prompt("Enter details: ")

        #  check the input
        if not headline or not category or not region or not details:
            print("All fields are required.")
            return

        payload = {
            "headline": headline,
            "category": category,
            "region": region,
            "details": details
        }

        try:
            response_url = self.news_service_url + "api/stories"
            print(response_url)
            print(payload)
            response = self.session.post(response_url, json=payload)
            response.raise_for_status()
            print("Story posted successfully.")
        except requests.RequestException as e:
            print("Failed to post story:", str(e))

    def get_news(self, command):
        if not command.startswith("news"):
            print("Invalid command.")
            return

        valid_categories = {'pol', 'art', 'tech', 'trivia'}
        valid_regions = {'uk', 'eu', 'w'}
        params_dict = {"id": "*", "cat": "*", "reg": "*", "date": "*"}

        words = command.split()
        if len(words) > 1:
            params = words[1:]
            for param in params:
                try:
                    key, value = param.split("=")
                    key = key.strip("-")
                    if key in params_dict:
                        if key == "cat" and value not in valid_categories:
                            print(f"Invalid category: {value}")
                            return
                        if key == "reg" and value not in valid_regions:
                            print(f"Invalid region: {value}")
                            return
                        if key == "date":
                            # Validate and format date
                            try:
                                datetime.strptime(value, "%d/%m/%Y")
                            except ValueError:
                                print("Invalid date format. Use dd/mm/yyyy.")
                                return
                        params_dict[key] = value
                    else:
                        print(f"Invalid parameter: {key}")
                        return
                except ValueError:
                    print("Error in parameter formatting. Use -key=value format.")
                    return

        url = "https://newssites.pythonanywhere.com/api/directory/"
        response = self.session.get(url)
        if response.status_code != 200:
            print("Failed to fetch agencies directory.")
            return

        agencies = response.json()
        agencies_list = {agency['agency_code']: agency for agency in agencies}

        all_stories = []
        for code, agency in agencies_list.items():
            try:
                if params_dict['id'] != "*" and params_dict['id'] != code:
                    continue

                agency_url = f"{agency['url'].rstrip('/')}/api/stories"
                stories_response = self.session.get(agency_url, params={
                    "story_cat": params_dict['cat'] if params_dict['cat'] != "*" else None,
                    "story_region": params_dict['reg'] if params_dict['reg'] != "*" else None,
                    "story_date": params_dict['date'] if params_dict['date'] != "*" else None,
                })

                if stories_response.status_code == 200:
                    stories = stories_response.json().get('stories', [])
                    all_stories.extend(stories)
                    for story in stories:
                        self.print_story_details(story)
                else:
                    print(f"Error retrieving stories from {agency['url']}: HTTP {stories_response.status_code}")
            except requests.RequestException as e:
                print(f"Failed to fetch stories from {agency['url']}: {str(e)}")

    def print_story_details(self, story):
        print(f"Key: {story.get('key')}")
        print(f"Headline: {story.get('headline')}")
        print(f"Category: {story.get('story_cat')}")
        print(f"Region: {story.get('story_region')}")
        print(f"Author: {story.get('author')}")
        print(f"Date: {story.get('story_date')}")
        print(f"Details: {story.get('story_details')}")
        print("-" * 30)

    def list_agencies(self):
        try:
            response = requests.get(BASE_URL + "directory/")
            response.raise_for_status()
            agencies_list = response.json()
            if agencies_list:
                for agency in agencies_list:
                    print("Agency Name:", agency.get("agency_name", "N/A"))
                    print("URL:", agency.get("url", "N/A"))
                    print("Agency Code:", agency.get("agency_code", "N/A"))
                    print()
            else:
                print("No agencies found.")
        except requests.RequestException as e:
            print("Failed to list agencies:", str(e))

    def delete_story(self, command):
        story_key = command.split()[1]
        if not self.logged_in:
            print("Please login first.")
            return

        if not story_key:
            print("Invalid story key provided.")
            return

        try:
            response = self.session.delete(f"{self.news_service_url}/api/stories/{story_key}")
            response.raise_for_status()  # Will raise an HTTPError for non-200 responses
            print("Story deleted successfully.")
        except requests.HTTPError:
            print("Failed to delete story:", response.text)
        except requests.RequestException as e:
            print("Network error occurred:", str(e))

    def handle_command(self, command):
        if command.startswith("login"):
            self.login(command)
        elif command == "logout":
            self.logout()
        elif command == "post":
            self.post_story()
        elif command.startswith("news"):
            self.get_news(command)
        elif command == "list":
            self.list_agencies()
        elif command.startswith("delete"):
            self.delete_story(command)
        elif command == "exit":
            return True
        else:
            print("Invalid command.")
        return False


def main():
    client = Client()
    while True:
        command = input("Enter command (login + URL, logout, post, news, list, delete, exit): ")
        if client.handle_command(command):
            break


if __name__ == "__main__":
    main()
