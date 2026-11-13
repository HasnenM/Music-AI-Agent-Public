import os 
import json
from litellm import completion
from dotenv import load_dotenv
import inspect
import shutil
from tool_registry import register_tool, tools, tool_functions


# Phase 1: Song database, ratings and metadata -----------------------------------------------------------------------------------------------------------------------------

# Loads environment variables from the .env file.
load_dotenv()

# Path to the songs
path = os.getenv("SONGS_PATH")

if not path or not os.path.isdir(path):
    raise SystemExit(
        "Invalid SONGS_PATH. Check your .env file and make sure the folder exists."
    )

def scan_songs():
# Returns all scanned songs from the song folder 
    song_list = os.listdir(path)
    # Creates an empty dictionary to store the songs found in the folder.
    all_songs = {}
    # Adds each song to the dictionary using its name as the key.
    # The value is another dictionary containing the song's file path.
    for song in song_list:
        if song.lower().endswith((".mp3", ".wav")):
            all_songs[song] = {
                "file_path": os.path.join(path, song)} 
    return all_songs

# Dictionary containing all the songs found in the folder.
all_songs = scan_songs()

def json_song_checker(all_songs):
# Loads the songs from the JSON file. If the file is missing or empty, creates it using the scanned songs.
    if os.path.exists("all_songs.json") and os.path.getsize("all_songs.json") > 0:
     with open("all_songs.json", "r") as file:
        json_songs = json.load(file)
    # If the JSON file is missing or empty, save all the scanned songs into it.
    else:
        with open("all_songs.json", "w") as file:
            json.dump(all_songs, file, indent=4)
        json_songs = all_songs
    
    return json_songs
# Contains all the songs that are in the json file.
json_songs = json_song_checker(all_songs)


def remove_deleted_songs(all_songs, json_songs):
# Checks if new songs match any removed songs so their stats can be carried over.
# Unmatched removed songs are deleted and new songs are added without any existing stats.
    if not all_songs:
        print("No songs detected. Skipping database update to protect saved metadata.")
        return


    removed_songs = [
        song for song in json_songs
        if song not in all_songs
    ]

    new_songs = [
        song for song in all_songs
        if song not in json_songs
    ]

    new_songs_to_check = new_songs.copy()
    removed_songs_to_check = removed_songs.copy()

    removed_song_numbered = [
        f"{i}. {song}"
        for i, song in enumerate(removed_songs, start=1)
    ]

    # Compare new songs to removed songs.
    for new_song in new_songs_to_check:
        print(f"New song detected: {new_song}.")

        # If removed songs exist, ask whether the new song matches one.
        if removed_songs_to_check:
            print("Does this song match one of the removed songs?")

            for song in removed_song_numbered:
                print(song)

            song_number = input(
                "If it matches one of the songs, type the number, otherwise type no: "
            )

            # Keep asking until the user enters "no" or a valid number.
            while song_number != "no" and (not song_number.isdigit() or int(song_number) not in range(1, len(removed_song_numbered) + 1)):
                song_number = input("Please enter a valid number or no: ")
                for song in removed_song_numbered:
                    print(song)

            # If the song is completely new, add it without old metadata.
            if song_number == "no":
                json_songs[new_song] = all_songs[new_song]
                new_songs.remove(new_song)

            # Otherwise, transfer metadata from the matched song.
            else:
                index = int(song_number) - 1
                removed_song = removed_songs_to_check[index]

                json_songs[new_song] = json_songs[removed_song]
                json_songs[new_song]["file_path"] = all_songs[new_song]["file_path"]

                new_songs.remove(new_song)
                removed_songs.remove(removed_song)
                del json_songs[removed_song]

                removed_songs_to_check.remove(removed_song)

                removed_song_numbered = [
                    f"{i}. {song}"
                    for i, song in enumerate(removed_songs_to_check, start=1)
                ]

        # If no removed songs remain, add the new song normally.
        else:
            json_songs[new_song] = all_songs[new_song]
            new_songs.remove(new_song)

    # Delete removed songs that weren't matched.
    if removed_songs:
        removed_song_list = "\n".join(removed_songs)
        
        remove_confirmation = input(f"""The following songs are missing from your folder:
        {removed_song_list}
        
        Remove their metadata from the database? (yes/no): """).strip().lower()

        if remove_confirmation == "yes":
            shutil.copy2("all_songs.json", "all_songs_backup.json")
            # Delete removed songs that weren't matched.
            for removed_song in removed_songs:
                del json_songs[removed_song]
        else:
            print("Metadata preserved. No songs were deleted.")

    # Updates saved song file paths to match the current folder location while preserving existing metadata.
    for song in json_songs:
        if song in all_songs:
            json_songs[song]["file_path"] = all_songs[song]["file_path"]

    # Save updated song data.
    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

remove_deleted_songs(all_songs=all_songs, json_songs=json_songs)


@register_tool
def play_song(song: str, json_songs: dict):
    """Opens the selected song using its saved file path."""
    os.startfile(json_songs[song]["file_path"])

def song_rating(song, all_songs, json_songs, song_was_started):

# All the genres that the user can pick from to describe the song.
    all_genres = ["Hip-Hop / Rap", "Melodic Hip-Hop", "Pop", "R&B", "House / EDM", "Other"]

# If the song exists in the folder but not in the JSON file, add it to the JSON data.
    if song not in json_songs:
            json_songs[song] = all_songs[song]
# Plays the song if it has no rating or genre so the user can listen before choosing.
    if "rating" not in json_songs[song] or "genre" not in json_songs[song]:
            if song_was_started == False:
                play_song(song=song, json_songs=json_songs)
                song_was_started = True
# If the song has no rating, ask the user to rate it from 1-10.
    if "rating" not in json_songs[song]:
        while True:
            try:
                song_rating = float(input(f"How would you rate this song from 1-10? {song}\nRating: "))

                if song_rating > 10 or song_rating < 1:
                    print("Please pick a number from 1-10.")
                    continue

                break

            except ValueError:
                print("Please enter a valid number.")

        json_songs[song]["rating"] = song_rating
        with open("all_songs.json", "w") as file:
            json.dump(json_songs, file, indent=4)
            
# If the song has no notes saved, ask the user if they want to add any.
# Pressing Enter skips this step.
    if "notes" not in json_songs[song]:
        # If song has no notes and is not already playing play the song.
        if song_was_started == False:
            play_song(song=song, json_songs=json_songs)
            song_was_started = True
        notes_list = []
        notes = input(f"There are currently no notes for this song {song}.\nWould you like to add some notes? (Press Enter to skip)\nNotes: ").strip().split(".")
        for note in notes: 
            note = note.strip()
            if note != "":
                notes_list.append(note)
        json_songs[song]["notes"] = notes_list

# If the song has no genre, ask the user to select one or more genres using their numbers.
# Converts the selected numbers into genre names and saves them as a list.
    if "genre" not in json_songs[song]:
        song_genres = []
        genre_numbers = input(f"What genre is this song {song}? Pick from the following by entering the number.\nYou can pick multiple genres.\n1. Hip-Hop / Rap\n2. Melodic Hip-Hop\n3. Pop\n4. R&B\n5. House / EDM\n6. Other\nGenre: ").replace(",", " ").split()
        while all(number.isdigit() and 1 <= int(number) <= 6 for number in genre_numbers) != True or genre_numbers == []:
            print("1. Hip-Hop / Rap\n2. Melodic Hip-Hop\n3. Pop\n4. R&B\n5. House / EDM\n6. Other")
            genre_numbers = input("Please pick a valid number for the list provided: ").replace(",", " ").split()
        genre_indexes = []
        for numbers in genre_numbers:
            genre_indexes.append(int(numbers) - 1)
        for indexes in genre_indexes:
            song_genres.append(all_genres[indexes])


# Removes any extra spaces around the selected genre names using strip().
        cleaned_song_genres = []
        for genre in song_genres:
            clean_genre = genre.strip()
            cleaned_song_genres.append(clean_genre)
            json_songs[song]["genre"] = cleaned_song_genres

# If the genre is stored as a string, convert it into a list.
    if isinstance(json_songs[song]["genre"], str):
        json_songs[song]["genre"] = [json_songs[song]["genre"]]

# Checks if any saved genres are invalid and asks the user to correct them.
    song_genres_valid = False

    while song_genres_valid == False:
        song_genres_valid = True
        for genre in json_songs[song]["genre"]:
            if genre not in all_genres:
                song_genres_valid = False
        if song_genres_valid == False:
            new_genre = (input(f"Invalid genre detected for {song}. Please pick from the following: Hip-Hop / Rap, Melodic Hip-Hop, Pop, R&B, House / EDM, Other\nGenre: ").split(","))
            stripped_genre = []
            for genre in new_genre:
                stripped_genre.append(genre.strip())
            json_songs[song]["genre"] = stripped_genre
            

    with open("all_songs.json", "w") as file:
            json.dump(json_songs, file, indent=4)
            return song_was_started    


# PHASE 2 — SONG COMPLETION TRACKING ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def calculate_completion_stats(song, json_songs, song_was_started):#
# Collects completion percentages for each category if they haven't been saved.
# Calculates the overall completion score using all eight categories.
    completion_stats = {
                    "beat": 0,
                    "lyrics": 0,
                    "hook": 0,
                    "verse_1": 0,
                    "verse_2": 0,
                    "vocals": 0,
                    "adlibs": 0,
                    "final_mix":0}

    if "completion_stats" not in json_songs[song]:
        # Plays the song if it hasn't already been played during this process.
        if song_was_started == False:
            play_song(song=song, json_songs=json_songs)
            song_was_started = True
        print("Rate the completion of the following categories from 0-100 in increments of 10.")
        for category in completion_stats:
            while True:           
                try:
                    completion_number= int(input(f"{category}: "))
                    if completion_number > 100 or completion_number < 0:
                        print("Please give a number between 0-100.")
                        continue
                    break
                except ValueError:
                    print("Please enter a number between 0-100 in increments of 10.")
                    
            completion_number = completion_number / 10 
            completion_number = round(completion_number)
            completion_number = completion_number * 10 
            completion_stats[category] = completion_number
            json_songs[song]["completion_stats"] = completion_stats  
    # Calculates the overall completion score by averaging all eight categories.
    completion_score = 0
    for category in json_songs[song]["completion_stats"]:
        completion_score += json_songs[song]["completion_stats"][category]
    completion_score /= 8
    json_songs[song]["completion_score"] = completion_score      


    with open("all_songs.json", "w") as file:
            json.dump(json_songs, file, indent = 4)
    return song_was_started


def show_song_progress(json_songs):
# Displays all songs and lets the user select one to view its completion progress.
# Also shows which categories still need work.
    song_list_numbered = [song for song in json_songs]
    song_list = [song for song in json_songs]
    song_count = []
    does_it_need_more_work = True
    # Numbers the songs so the user can select one from the list.
    for i in range(0, len(song_list_numbered)):
        song_list_numbered[i] = f"{i}. {song_list_numbered[i]}"
        song_count.append(i)

    work_needed = []
    print("\nHere are all of your current songs")
    print("-------------------------------------")
    for song in song_list_numbered:
        print(f"{song}")
    song_number = int(input("show a song's progess by typing it's number: "))
    if song_number not in song_count:
        song_number = int(input("That song does not exist. Pick one of the song number's provided: "))
    picked_song = song_list[song_number]
    print(f"\nSong progress for {picked_song} - {json_songs[picked_song]["completion_score"]}% Complete")
    print("-------------------------------------")
    if json_songs[picked_song]["completion_score"] == 100:
            print("This song is complete!")
            does_it_need_more_work = False
    for category in json_songs[picked_song]["completion_stats"]:
        # Prints all the categories and their values.
        print(f"{category}: {json_songs[picked_song]["completion_stats"][category]}%")
        # Adds any categories below 100% to the list of work that still needs doing.
        if json_songs[picked_song]["completion_stats"][category] < 100:
            work_needed.append(category)

    if does_it_need_more_work == True:
        print("")
        print("Work needed:")
        print("-------------------------------------")
        work_required = ", ".join(work_needed).replace("_", " ")
        print(work_required)

def process_songs(all_songs, json_songs):
    # Goes through every song and collects any missing ratings, genres, notes and completion stats.
    for song in all_songs:
        song_was_started = False
        song_was_started = song_rating(song=song, json_songs=json_songs, all_songs= all_songs, song_was_started= song_was_started)
        song_was_started = calculate_completion_stats(song=song, json_songs=json_songs, song_was_started= song_was_started)

process_songs(all_songs=all_songs, json_songs=json_songs)



# PHASE 3 Agent Integration -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Retrieves the OpenAI API key from the environment.
api_key = os.getenv("OPENAI_API_KEY")

from typing import Literal, Union


@register_tool
def agent_song_info(song: str, json_songs: dict):
    """Returns all the saved information for the selected song as a dictionary."""
    agent_song = json_songs[song]
    return agent_song


@register_tool
def agent_all_songs_info(json_songs: dict):
    """Returns all songs' information in JSON format."""
    return json_songs


def tool_executor(tool_name, tool_args, json_songs):
    # Uses the tool name to retrieve the corresponding Python function.
    tool_used = tool_functions[tool_name]

    # Inspects the selected function and returns the parameters it requires.
    parameters_needed = inspect.signature(tool_used).parameters

    # Creates a dictionary containing all available parameters and their values.
    # tool_args are provided by the LLM, while json_songs is provided by Python.
    parameter_dictionary = {
        **tool_args,
        "json_songs": json_songs
    }

    # Creates a dictionary to store the arguments needed by the selected function.
    parameter_used = {}

    # Matches each parameter name to its value.
    for parameter in parameters_needed:
        if parameter in parameter_dictionary:
            parameter_used[parameter] = parameter_dictionary[parameter]

    # Passes the arguments by name and executes the selected tool.
    try:
        tool_result = tool_used(**parameter_used)
    except Exception as error:
        tool_result = f"Tool execution failed: {error}"

    # Returns the result from the selected tool.
    return tool_result


def song_name_picker(song, json_songs):
    # Searches for songs that match the name provided by the user.
    # Returns None, one song name or a list of matching songs.

    song_picked = []
    for song_name in json_songs:
        if song.lower() in song_name.lower():
            song_picked.append(song_name)
    if len(song_picked) > 1:
        return song_picked
    if len(song_picked) == 0:
        return None
    else:
        return song_picked[0]


@register_tool
def update_song_progress(
    user_category: Literal[
        "beat", "lyrics", "hook", "verse_1",
        "verse_2", "vocals", "adlibs", "final_mix"
    ],
    new_value: int,
    song: str,
    json_songs: dict
):
    """Updates the completion progress of a song based on the user input."""

    if new_value > 100 or new_value < 0:
        return "Invalid number detected, number has to be between 0-100"
    else:
        new_value = round(new_value / 10) * 10
        if user_category in json_songs[song]["completion_stats"]:
            json_songs[song]["completion_stats"][user_category] = new_value
        else:
            return "Invalid completion category"

        completion_score = 0
        for category in json_songs[song]["completion_stats"]:
            completion_score += json_songs[song]["completion_stats"][category]
        completion_score /= 8
        json_songs[song]["completion_score"] = completion_score

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)
        return new_value


@register_tool
def update_song_genre(
    song: str,
    json_songs: dict,
    user_genre: list[
        Literal[
            "Hip-Hop / Rap", "Melodic Hip-Hop", "Pop",
            "R&B", "House / EDM", "Other"
        ]
    ]
):
    """Updates the song's genres using a list that can contain multiple genres."""

    all_genres = ["Hip-Hop / Rap", "Melodic Hip-Hop", "Pop", "R&B", "House / EDM", "Other"]
    for genre in user_genre:
        if genre not in all_genres:
            return f"Invalid genre detected, user has to pick from the following genres: {all_genres}"

    json_songs[song]["genre"] = user_genre
    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)
    return user_genre


@register_tool
def update_song_name(song: str, user_song: str, json_songs: dict):
    """
    Renames the song file in the folder and updates its name and file path in the JSON data.
    The song parameter may contain a partial song name.
    The user_song parameter must contain the new name requested by the user.
    """

    old_path = os.path.join(path, song)
    file_extension = os.path.splitext(song)[1]
    new_song = os.path.splitext(user_song)[0] + file_extension
    new_path = os.path.join(path, new_song)

    if os.path.exists(new_path):
        return "A song with that name already exists."

    os.rename(old_path, new_path)
    json_songs[new_song] = json_songs[song]
    json_songs[new_song]["file_path"] = new_path
    json_songs.pop(song)

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return new_song


@register_tool
def add_song_notes(song: str, user_notes: list[str], json_songs: dict):
    """
    Add notes to the song provided by the user and update this in the JSON file.
    Identify the song title and note text separately.
    The song parameter must contain only the song title.
    The user_notes parameter must contain only the text the user wants to save.
    When confirming the song update always use the exact file name returned by the tool.
    """

    full_notes = json_songs[song]["notes"]
    valid_notes = [
        note for note in user_notes
        if isinstance(note, str) and note.strip()
    ]

    if not valid_notes:
        return "No notes were added because the provided notes were empty."

    json_songs[song]["notes"].extend(valid_notes)
    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return f"""Notes added to {song}\n
               Here are the full notes:{full_notes} for {song}."""


@register_tool
def remove_song_notes(
    song: str,
    note_number: Union[int, str],
    json_songs: dict
):
    """
    Remove notes from a song.
    Use a note number starting at 1, or 'all' to remove every note.
    After removing notes, display the updated notes as a numbered list.

    Args:
        song: The song's name.
        note_number: A note number, or 'all' to remove every note.
    """

    full_notes = json_songs[song]["notes"]

    if note_number == "all":
        json_songs[song]["notes"].clear()
        with open("all_songs.json", "w") as file:
            json.dump(json_songs, file, indent=4)
        return f"Removed all the notes for{song}"

    if not isinstance(note_number, int):
        return "Invalid note number. Please provide a number."

    note_index = note_number - 1
    if note_index not in range(0, len(json_songs[song]["notes"])):
        return f"Note {note_number} does not exist for {song}. No notes were removed. Available notes: {full_notes}."
    note = json_songs[song]["notes"][note_index]
    del json_songs[song]["notes"][note_index]

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return f"""Note {note_number}.{note} removed from {song}\n
               Here are the all the full notes: {full_notes} for {song}"""


@register_tool
def add_song_tasks(song: str, json_songs: dict, tasks: list[str]):
    """
    Only generate tasks when the song's notes clearly suggest
    an action, improvement, or unfinished work.
    Do not turn positive feedback or observations into tasks
    unless the user explicitly requests an action.
    If no genuinely new actionable tasks exist, do not add any.
    """

    added_tasks = []
    duplicate_tasks = []

    if "tasks" not in json_songs[song]:
        json_songs[song]["tasks"] = []

    for task in tasks:
        duplicate_found = False

        for existing_tasks in json_songs[song]["tasks"]:
            if task == existing_tasks["task"]:
                duplicate_tasks.append(task)
                duplicate_found = True

        if duplicate_found == False:
            added_tasks.append(task)
            json_songs[song]["tasks"].append({
                "task": f"{task}",
                "completed": False
            })

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return f"""New tasks that got added: {added_tasks}
               Duplicate tasks found: {duplicate_tasks}
               Updated tasks {json_songs[song]["tasks"]}"""


@register_tool
def remove_song_tasks(
    song: str,
    json_songs: dict,
    task_number: Union[int, str]
):
    """
    Remove tasks from a song as requested by the user.

    Args:
        song: The song's name.
        task_number: A task number starting at 1, or 'all' to remove every task.
    """

    all_tasks = json_songs[song].get("tasks", [])

    if task_number == "all":
        all_tasks.clear()
        with open("all_songs.json", "w") as file:
            json.dump(json_songs, file, indent=4)
        return f"Removed all the tasks for {song}"

    if not isinstance(task_number, int):
        return "Invalid task number. Please provide a number."

    task_index = task_number - 1
    if task_index not in range(0, len(all_tasks)):
        return f"Task {task_number} does not exist for {song}. No tasks were removed. Available tasks: {all_tasks}."

    task = all_tasks[task_index]
    del all_tasks[task_index]

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return f"""Task {task_number}.{task} removed from {song}\n
               Here are the all the tasks: {all_tasks} for {song}"""


@register_tool
def update_song_tasks(
    song: str,
    json_songs: dict,
    task_number: int,
    tasks: str = None,
    completed: bool = None
):
    """
    Update an existing song task's description or completion status.

    The task_number MUST be the exact number the user requested.
    Never substitute another task number, even if the requested number does not exist.
    If the user requests task 99, pass task_number=99, NOT a valid alternative.
    The Python function will handle invalid task numbers.

    Use tasks to change the description.
    Use completed to mark the task as done or not done.
    """

    if not isinstance(task_number, int):
        return "Invalid task number. Please provide a number."

    task_index = task_number - 1
    all_tasks = json_songs[song].get("tasks", [])

    if task_index not in range(0, len(all_tasks)):
        return f"Task {task_number} does not exist for {song}. No tasks were changed. Available tasks: {all_tasks}. Clearly explain to the user that the requested task number is invalid."

    if tasks != None:
        all_tasks[task_index]["task"] = tasks

    if completed != None:
        all_tasks[task_index]["completed"] = completed

    with open("all_songs.json", "w") as file:
        json.dump(json_songs, file, indent=4)

    return f"Updated task: {all_tasks[task_index]}."


# System instructions that define the agent's purpose and behaviour.
agent_rules = [{
    "role": "system",
    "content": """
    You are an AI Music agent bot. You are connected to a database of song's which are all made by the user. The user is a musician who is using the app to store all types of information
    regarding their songs such as: rating, genre and it also has a section showing how complete the song is with these categories: beat, lyrics, hook, verse_1, verse_2, vocals, adlibs
    and final_mix. The user's main goal is to get more song's complete as they get overwhelmed by all this information. The song's with the highest rating's should be prioritised.
    Respond using plain text only. Do not use Markdown formatting such as **, #, or backticks. Display song notes as a numbered list, with each note on a seperate line.
    Whenever the user asks to view, add, edit, complete, or remove song information or tasks, you MUST call the appropriate tool before responding. Never claim a task exists, 
    has changed, or does not exist without checking the database using a tool. Song names may be partial names.
    """
}]

# Combines the agent's system instructions with the conversation history.
messages = agent_rules 

print("🎵 Welcome to your Music AI Agent!")
print("What would you like help with today?\n")

while True:
    # Captures the user's input 
    user_task = input("You: ")

    # Stores the user's input in a message dictionary.
    memory = {"role": "user", "content": user_task}

    # Adds the user's message to the conversation history.
    messages.append(memory)


    # Sends the conversation and available tools to the LLM.
    response = completion(
        model="openai/gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=1024,
        api_key=api_key
    )

    while response.choices[0].message.tool_calls is not None:

        # Retrieves the tool call selected by the LLM.
        tool_calls = response.choices[0].message.tool_calls

        # Adds the LLM's tool request to the conversation history before executing it.
        messages.append(response.choices[0].message)

        for tool in tool_calls:

            # Extracts the name of the tool the LLM selected.
            tool_name = tool.function.name

            # Converts the LLM's JSON arguments into a Python dictionary.
            tool_args = json.loads(tool.function.arguments)
  
            # Checks if the tool's args require a song name.
            if "song" not in tool_args:
                tool_result = tool_executor(tool_name, tool_args, json_songs)
            else: 
                # Checks the song name and returns None, one matching song or a list of matching songs.
                song_name = song_name_picker(song=tool_args["song"], json_songs=json_songs)
                
                # If song_name is a list that means there are multiple matches and the exact song should be clarified by the user.
                if type(song_name) == list:
                    tool_result = f"Multiple songs detected ask the user to clarify which song they want out of the matching songs: {song_name} "

                # If no song matches, tell the LLM to ask the user for the correct song name.
                elif song_name == None: 
                    tool_result = f"No songs detected ask the user to clarify which song they want."

                # If one song matches, use its full name when calling the tool.
                else:

                    # Replaces the user's partial song name with the full matching name.
                    tool_args["song"] = song_name
    
                    # Executes the selected tool using the full song name and stores its result.
                    tool_result = tool_executor(tool_name, tool_args, json_songs)

            # Formats the Python function's result as a tool response
            # that can be sent back to the LLM.
            agent_result = {
                "role": "tool",
                "tool_call_id": tool.id,
                "content": json.dumps(tool_result)
            }
            
            # Adds the tool's result to the conversation so the LLM can use it.
            messages.append(agent_result)

        # Sends the updated conversation back to the LLM so it can use the tool result.
        response = completion(
            model="openai/gpt-4o",
            messages=messages,
            tools=tools,
            max_tokens=1024,
            api_key=api_key
        )

    llm_final_response = {"role": "assistant", "content": response.choices[0].message.content} 

    messages.append(llm_final_response)

    # Prints the LLM's final response after it has received the tool result.
    print(f"Agent: {response.choices[0].message.content}")






# # \n
