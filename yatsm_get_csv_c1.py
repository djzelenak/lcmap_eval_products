import os, sys, fnmatch, pprint
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", type=str, required=True, help="Full path to stacked ARD imagery")
parser.add_argument("-o", "--output", type=str, required=True, help="Full path to output folder")

args = parser.parse_args()

inputDir = args.input
outputDir = args.output

if not os.path.exists(outputDir):
    os.makedirs(outputDir)


# %%
def get_date(date):
    """Convert YYYYMMDD to YYYY+DOY
    
    Args:
        date = YYYYMMDD format (string)
    Return:
        yyyydoy = string object containing year and day of year
    """

    day = int(date[-2:])
    month = str(date[-4:-2])
    year = float(date[:4])

    if (year // 4 == year / 4):
        y = 1

    # elif (year//100 == year/100): y = 1

    else:
        y = 0

    month_len = {'01': 0, '02': 31, '03': 59, '04': 90, '05': 120, '06': 151, '07': 181,
                 '08': 212, '09': 243, '10': 273, '11': 304, '12': 334}

    if y == 1 and int(month) >= 3:
        monthdays = month_len[month] + 1
        doy = monthdays + day

        if len(str(doy)) < 2:
            yyyydoy = str(int(year)) + '00' + str(doy)
        elif len(str(doy)) < 3:
            yyyydoy = str(int(year)) + '0' + str(doy)
        else:
            yyyydoy = str(int(year)) + str(doy)
    else:
        monthdays = month_len[month]
        doy = monthdays + day

        if len(str(doy)) == 1:
            yyyydoy = str(int(year)) + '00' + str(doy)
        elif len(str(doy)) == 2:
            yyyydoy = str(int(year)) + '0' + str(doy)
        else:
            yyyydoy = str(int(year)) + str(doy)

    return yyyydoy


# %%
imagefolders = []
for dirpath, folders, files in os.walk(inputDir):
    for folder in folders:
        if fnmatch.fnmatch(folder, 'L*'):
            # images.append(dir + os.sep + folder)
            imagefolders.append(os.path.join(dirpath, folder))

imagenames = []
for f in imagefolders:
    for dirpath, folders, files in os.walk(f):
        for filef in files:
            if fnmatch.fnmatch(filef, "*MTLstack.tif"):
                imagenames.append(filef)

imagefolders.sort()
imagenames.sort()
# %%
imagedates = []
for x in imagenames:
    c1date = x[15:23]
    YYYYDOY = get_date(c1date)
    imagedates.append(YYYYDOY)

# %%
imagesensor = []
for y in imagenames:
    sensor = y[0:4]
    sensor = sensor.replace("0", "")
    imagesensor.append(sensor)
# %%
masterlist = []
for z in range(0, len(imagefolders)):
    masterlist.append(imagedates[z] + ',' + imagesensor[z] + ',' + imagefolders[z] + os.sep + imagenames[z])

masterlist.sort()
print('folders:')
pprint.pprint(imagefolders)
pprint.pprint(imagenames)
pprint.pprint(imagedates)
pprint.pprint(imagesensor)
pprint.pprint(masterlist)

print(len(imagefolders))
print(len(imagenames))
if len(imagefolders) != len(imagenames):
    print("Length of image folders doesn't equal length of image names!")
    sys.exit(1)

f = open(outputDir + os.sep + 'images.csv', 'w')
f.write('date,sensor,filename\n')
for l in range(0, len(imagefolders)):
    # f.write(imagedates[l] + ',' + imagesensor[l] + ',' + images[l] + os.sep + imagenames[l]+ '\n')
    # f.write('%s,%s,%s/%s\n' %(imagedates[l], imagesensor[l], images[l], imagenames[l]))
    f.write(masterlist[l] + '\n')
f.close()


