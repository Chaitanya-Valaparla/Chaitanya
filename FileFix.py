import os
import numpy as np
import time
import datetime
import Constants as c
import HelperFunctions as hf

c = Constants()
hf = HelperFunctions()


while True:
    date_time = datetime.datetime.now()

    dirFormat = format(date_time.year,date_time.month,date_time.day))
    rawformat = format(date_time.year,date_time.month,date_time.day,events)
    fixedFormat = format(date_time.year,date_time.month,date_time.day,events[3:])
    dirsToCreate('c.ABSOLUTE_PATH/fixed/{0}_{1}_{2}'.dirFormat, 'c.ABSOLUTE_PATH/raw/{0}_{1}_{2}'.dirFormat)
    for pathDir in dirsToCreate:
        hf.endureAndCreateDirectory(pathDir)

    

    event_list = os.listdir('c.ABSOLUTE_PATH/fixed/raw/{0}_{1}_{2}'.dirFormat

    for events in event_list:
        raw_filename = '/home/pi/AccelData/raw/{0}_{1}_{2}/{3}'.rawFormat
        fix_filename = '/home/pi/AccelData/fixed/{0}_{1}_{2}/{3}'.fixedFormat
        if os.path.exists(raw_filename) and not os.path.exists(fix_filename):
            time.sleep(1)
            data = np.loadtxt(raw_filename, delimiter=',')  # Import data from event as numpy array
            try:
                i = int(data[c.EVENT_TRIGGER_LOC, 0])  # Pull the trigger index
            except IndexError as q:
                print('Index Error: {}'.format(q))
                break
            except:
                print('Something Went Wrong')
                break

            fixed_data = np.zeros(shape=(c.NUM_ACCEL_BUFFER_ROWS, c.NUM_ACCEL_BUFFER_COLUMNS))  # Create an empty array for fixed data

            ################################################################################
            # Step one:
            # Find 'true zero' in the input data.
            # Input: i, the index of the event in the circular buffer
            # Output: zero, the index of the beginning of relevant data (1 second prior to event)
            ################################################################################
            zero = 0
            if i < ONE_SEC:
                zero = i + TWO_SEC
            else:
                zero = i - ONE_SEC

            ################################################################################
            # Step two:
            # Copy the 1200 values following the true zero in the circular buffer into the output array.
            # Input: zero, the index of the beginning of relevant data (1 second prior to event)
            # Input: data, the circular buffer captured during and after the event
            # Output: outArray, an organized array containing data from 1 second before, and 2 seconds after the event
            ################################################################################
            for counter in range(1200):
                shiftedIndex = zero + counter

                if shiftedIndex >= EVENT_TRIGGER_LOC:
                    shiftedIndex -= EVENT_TRIGGER_LOC

                fixed_data[counter] = data[shiftedIndex]

            max_val = np.max(fixed_data, axis=0)
            min_val = np.min(fixed_data, axis=0)

            print('Max Values: ')
            print(max_val)
            print('Min Values: ')
            print(min_val)

            ab_max = np.maximum(np.absolute(max_val), np.absolute(min_val))

            print("Absolute Max: ")
            print(ab_max)

            fixed_data[1200] = [ab_max[0], ab_max[1], ab_max[2]]

            np.savetxt(fix_filename, fixed_data, delimiter=',', newline='\n', fmt='%3.4f')  # Write out the fixed data

            event_stamp = events[9:]
            event_stamp = event_stamp[:-4]
            event_hour = int(event_stamp.rsplit('_')[0])
            event_minute = int(event_stamp.rsplit('_')[1])
            event_second = int(event_stamp.rsplit('_')[2])

            timestamp = '{:02d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(int(date_time.month),
                                                                           int(date_time.day),
                                                                           int(date_time.year),
                                                                           event_hour,
                                                                           event_minute,
                                                                           event_second)
            print(timestamp + '\n')

            file = open(fix_filename, "a")
            file.write("{}\n".format(os.uname()[1]))
            file.write("{}\n".format(timestamp))
            file.close()

    time.sleep(.5)
