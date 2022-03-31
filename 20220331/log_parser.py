# Before running this script:
#   1. Install the pandas module using `pip install pandas`.
#   2. Make sure that the file `TRIAL LOGS.xlsx` is in the same directory.
#   3. In `TRIAL LOGS.xlsx`, manually append the logs in sheet `S00(t5_t12)` to
#      `S00(t1_t4)`, rename `S00(t1_t4)` as `S00`, and delete `S00(t5_t12)`.
#      This will ensure that all sheet names refer to the actual subject IDs.
#
# INPUT
# * TRIAL LOGS.xlsx
#
# OUTPUT
# * parsed_logs_quizzes.csv
# * parsed_logs_summary.csv


# Import csv and pandas modules.
import csv
import pandas as pd


# Declare source and destination file names.
SRC_FILE = 'TRIAL LOGS.xlsx'
DST_FILES = {
    'quizzes': 'parsed_logs_quizzes.csv',
    'summary': 'parsed_logs_summary.csv'
}

# Declare an empty dictionary where the processed data can be stored.
data = {}

# get_default_trial_checker_dict returns a dictionary containing the default
# values of the checkers and counters used in each trial.
def get_default_trial_checker_dict():
    return {
        'is_trial': False,
        'start_time': 0,
        'end_time': 0,

        'gesture_move_counter': 0,
        'gesture_rotate_counter': 0,
        'voice_drop_counter': 0,
        'voice_rotate_counter': 0,

        'quiz_counter': 0,
        'quizzes': {},
        'quizzes_total_time': 0,
        'quizzes_total_score': 0,
    }

# get_default_quiz_checker_dict returns a dictionary containing the default
# values of the checkers and counters used in each quiz.
def get_default_quiz_checker_dict():
    return {
        'is_quiz': False,
        'start_time': 0,
        'end_time': 0,
        'is_correct': False,
        'input_type': None,
    }

# Read all sheets in the source file.
df = pd.read_excel(
    SRC_FILE,
    sheet_name=None,
    header=None
)

# Store the sheet names in sheets.
sheets = df.keys()

# Loop through all the sheets.
for key in sheets:
    # Declare an empty dictionary inside the data variable
    # using the sheet name as key.
    data[key] = {}

    # Declare an integer named trial_counter which counts the number of trials
    # per subject.
    trial_counter = 0

    # Declare a dictionary named trial_checker that contains all the variables
    # used to count and check the trial-related logs per sheet.
    trial_checker = get_default_trial_checker_dict()

    # Declare a dictionary named quiz_checker that contains all the variables
    # used to count and check the quiz-related logs per sheet.
    quiz_checker = get_default_quiz_checker_dict()

    # Remove the blank rows in the logs.
    sheet = df[key].dropna()

    # Create columns time and log based on the first column
    # that contains the raw logs.
    #
    # Raw log: '952.5871227 - Start Task'
    # Format: '<time> - <log>
    first_column = sheet.iloc[:, 0]
    sheet[['time', 'log']] = sheet.iloc[:, 0].str.split(' - ', 1, expand=True)

    # Reset the sheet's index and iterate through each row.
    sheet = sheet.reset_index()
    for index, row in sheet.iterrows():
        # If the log contains the string `Start Task`:
        if 'Start Task' in row['log']:
            # Add 1 to the trial counter only if there are no ongoing trials
            # yet. This ensures that each trial will only be
            # counted once in case of duplicate `Start Task` logs.
            if trial_checker['is_trial'] == False:
                trial_counter += 1

            # Start a new trial and get its start time.
            #
            # Note that the start_time of the last log will be used
            # in case of duplicate `Start Task` logs.
            trial_checker['is_trial'] = True
            trial_checker['start_time'] = float(row['time'])
        
        # Add 1 to the trial_checker's gesture counters if the log contains the
        # string `Gesture` together with `Move` or `Rotate`.
        if 'Gesture' in row['log']:
            if 'Move' in row['log']:
                trial_checker['gesture_move_counter'] += 1
            if 'Rotate' in row['log']:
                trial_checker['gesture_rotate_counter'] += 1
        
        # Add 1 to the trial_checker's voice counters if the log contains the
        # string `Voice` together with `Drop` or `Rotate`.
        if 'Voice' in row['log']:
            if 'Drop' in row['log']:
                trial_checker['voice_drop_counter'] += 1
            if 'Rotate' in row['log']:
                trial_checker['voice_rotate_counter'] += 1
        
        # If the log contains the string `Open Quiz`:
        if 'Open Quiz' in row['log']:
            # Add 1 to the trial_checker's quiz counter only if there are no
            # ongoing quizzes yet. This ensures that each quiz will only be
            # counted once in case of duplicate `Open Quiz` logs.
            #
            # Note that the quiz counter is in the trial_checker instead of the
            # quiz_checker because the total number of quizzes is a data point
            # that is monitored per trial.
            if quiz_checker['is_quiz'] == False:
                trial_checker['quiz_counter'] += 1
            
            # Start a new quiz and get its start time.
            #
            # Note that the start_time of the last log will be used
            # in case of duplicate `Open Quiz` logs.
            quiz_checker['is_quiz'] = True
            quiz_checker['start_time'] = float(row['time'])
        
        # If the log contains the string `Answer`
        # while there is an ongoing quiz:
        if 'Answer' in row['log'] and quiz_checker['is_quiz']:
            # Set the quiz checker's correct answer checker to True.
            #
            # TODO: What if there are multiple `Answer` logs in a quiz?
            if 'Correct' in row['log']:
                quiz_checker['is_correct'] = True

            # Check if the input type used in the quiz is `Gesture` or `Voice.`
            if 'Gesture' in row['log']:
                quiz_checker['input_type'] = 'gesture'
            if 'Voice' in row['log']:
                quiz_checker['input_type'] = 'voice'
        
        # If the log contains the string `Close Quiz`
        # while there is an ongoing quiz:
        if 'Close Quiz' in row['log'] and quiz_checker['is_quiz']:
            # Get the quiz checker's end time and determine the total duration
            # of the quiz by subtracting the end time from the start time.
            quiz_checker['end_time'] = float(row['time'])
            total_time = quiz_checker['end_time'] - quiz_checker['start_time']

            # Record the quiz info under the trial checker's quizzes dictionary
            # using the quiz number as key.
            trial_checker['quizzes'][trial_checker['quiz_counter']] = {
                'total_time': total_time,
                'score': int(quiz_checker['is_correct']),
                'input_type': quiz_checker['input_type']
            }

            # Add the duration and score of the current quiz to the total
            # duration and score of the quizzes throughout the trial.
            trial_checker['quizzes_total_time'] += total_time
            trial_checker['quizzes_total_score'] += quiz_checker['is_correct']

            # Reset the quiz checker's values.
            quiz_checker = get_default_quiz_checker_dict()
        
        # If the log contains the string `Quit Task`
        # while there is an ongoing trial:
        if 'Quit Task' in row['log'] and trial_checker['is_trial']:
            # Get the trial checker's end time and determine the total duration
            # of the trial by subtracting the end time from the start time.
            trial_checker['end_time'] = float(row['time'])
            total_time = trial_checker['end_time'] - trial_checker['start_time']

            # Get the total number of quizzes throughout the trial and its
            # corresponding average time spent to answer each question and
            # score percentage based on the number of correct answers.
            quizzes_total_questions = len(trial_checker['quizzes'])
            quizzes_average_time = 0
            quizzes_score_percentage = 0
            if quizzes_total_questions != 0:
                quizzes_average_time = trial_checker['quizzes_total_time'] / quizzes_total_questions
                quizzes_score_percentage = trial_checker['quizzes_total_score'] / quizzes_total_questions * 100

            # Save all the trial info to a dictionary using the trial number
            # as key.
            data[key][trial_counter] = {
                'total_time': total_time,
                'gesture_move_frequency': trial_checker['gesture_move_counter'],
                'gesture_rotate_frequency': trial_checker['gesture_rotate_counter'],
                'voice_drop_frequency': trial_checker['voice_drop_counter'],
                'voice_rotate_frequency': trial_checker['voice_rotate_counter'],
                'quizzes': trial_checker['quizzes'],
                'quizzes_total_time': trial_checker['quizzes_total_time'],
                'quizzes_total_questions': quizzes_total_questions,
                'quizzes_average_time': quizzes_average_time,
                'quizzes_total_score': trial_checker['quizzes_total_score'],
                'quizzes_score_percentage': quizzes_score_percentage,
            }

            # Reset the trial checker's values.
            trial_checker = get_default_trial_checker_dict()

# This section formats the data generated from the first part of the script in
# order to save it as a CSV output.

# Create a copy of the data dictionary.
parsed_data = data

# Declare the columns to be used in the first CSV file.
csv_columns = [
    'subject_id',
    'trial_no',
    'total_time',
    'gesture_move_frequency',
    'gesture_rotate_frequency',
    'voice_drop_frequency',
    'voice_rotate_frequency',
    'quizzes_total_time',
    'quizzes_total_questions',
    'quizzes_average_time',
    'quizzes_total_score',
    'quizzes_score_percentage'
]

# Loop through each subject, trial, and quiz, and append each iteration to the
# csv_data list.
csv_data = []
for subject in parsed_data:
    for trial in parsed_data[subject]:
        trial_data = parsed_data[subject][trial]
        csv_data.append({
            'subject_id': subject,
            'trial_no': trial,
            'total_time': trial_data['total_time'],
            'gesture_move_frequency': trial_data['gesture_move_frequency'],
            'gesture_rotate_frequency': trial_data['gesture_rotate_frequency'],
            'voice_drop_frequency': trial_data['voice_drop_frequency'],
            'voice_rotate_frequency': trial_data['voice_rotate_frequency'],
            'quizzes_total_time': trial_data['quizzes_total_time'],
            'quizzes_total_questions': trial_data['quizzes_total_questions'],
            'quizzes_average_time': trial_data['quizzes_average_time'],
            'quizzes_total_score': trial_data['quizzes_total_score'],
            'quizzes_score_percentage': trial_data['quizzes_score_percentage']
        })
            

# Save the csv columns and data to the first destination file.
csv_file = DST_FILES['summary']
with open(csv_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    for d in csv_data:
        writer.writerow(d)

# Declare the columns to be used in the second CSV file.
csv_columns = [
    'subject_id',
    'trial_no',
    'quiz_no',    
    'quiz_total_time',
    'quiz_score',
    'quiz_input_type'
]

# Loop through each subject, trial, and quiz, and append each iteration to the
# csv_data list.
csv_data = []
for subject in parsed_data:
    for trial in parsed_data[subject]:
        for quiz in parsed_data[subject][trial]['quizzes']:
            quiz_data = parsed_data[subject][trial]['quizzes'][quiz]
            csv_data.append({
                'subject_id': subject,
                'trial_no': trial,
                'quiz_no': quiz,
                'quiz_total_time': quiz_data['total_time'],
                'quiz_score': quiz_data['score'],
                'quiz_input_type': quiz_data['input_type']
            })

# Save the csv columns and data to the second destination file.
csv_file = DST_FILES['quizzes']
with open(csv_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    for d in csv_data:
        writer.writerow(d)