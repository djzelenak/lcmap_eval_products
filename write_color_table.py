'''
Author: Dan Zelenak
Date: 3/8/2017
Purpose: Take a color table exported from ArcMap and convert it
into XML as a new .txt file to be used by GDAL.
'''

#ffile = r'C:\Users\dzelenak\Workspace\Sample_Data\CCDC_ChangeAccum\values0-32.clr'
#newfile = r'C:\Users\dzelenak\Workspace\Sample_Data\CCDC_ChangeAccum\change_accum_color_table.txt'

ffile = input("Enter full path to the .clr table: ")
newfile = input("Enter full path for the output .txt XML color table: ")

with open(ffile, 'r') as x, open(newfile, 'w') as y:
    y.write('   <ColorInterp>Palette</ColorInterp>\n'\
            '   <ColorTable>\n')
    for line in x:
        line = line.strip() #remove any \n's
        a = line.split(' ') #make a list of the items in line
        del(a[0]) #remove first item from list
        a.insert(0, '   <Entry c1=') #insert item at beginning of list a
        a.append('/>') #add item to the end of list a

        #use string formatting to rewrite items in list 'a' as a string
        #with the additional characters needed for the color table
        b = '{0}"{1}" c2="{2}" c3="{3}" c4="255"{4}\n'.format(a[0],a[1],a[2],a[3],a[4])

        y.write(b) #write the string b to the output color table

    #write the final line to the color table
    y.write('   </ColorTable>\n')

quit()