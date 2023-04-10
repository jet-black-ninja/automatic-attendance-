
# import the necessary packages
#for video
from imutils.video import VideoStream
from imutils.video import FPS

#for recognition
import face_recognition
import imutils
import pickle
import time
import cv2 

#to generate file
import csv
# for led and time based work
import RPi.GPIO as GPIO
from datetime import datetime	

#libraries for eamil 
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
from email import encoders

#details 
email_from="attedancesystemmail@gmail.com"
password="bgrskhnszmdooqvh"

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "T_encodings.pickle"
encodingsS = "S_encodings.pickle"
GPIO.setmode(GPIO.BCM)
GPIO.setup(16,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)

# load the known faces and embeddings along with OpenCV's Haarcascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
dataS= pickle.loads(open(encodingsS, "rb").read())

# initialize the video stream and allow the camera sensor to warm up
#vs = VideoStream(src=2,framerate=10).start()
vs = VideoStream(usePiCamera=True,framerate=5,resolution=(1280,720)).start()
time.sleep(2.0)

# start the FPS counter
#fps = FPS().start()


# loop over frames from the video file stream
while True:
	
	if GPIO.input(16)==1:
		GPIO.output(13,True)
		time.sleep(0.5)
		print("Scan for teacher")
		GPIO.output(13,False)
		over=False
		#grab time
		now=datetime.now()
		current_date=now.strftime("%Y-%m-%d %H") 
		filename=current_date+'.csv'
		f=open(filename,'w',newline='')
		# grab the frame from the threaded video stream and resize it
		# to 500px (to speedup processing)
		frame = vs.read()
		frame = imutils.resize(frame, width=500)
		# Detect the fce boxes
		boxes = face_recognition.face_locations(frame)
		# compute the facial embeddings for each face bounding box
		encodings = face_recognition.face_encodings(frame, boxes)
		names = []
		# loop over the facial embeddings
		for encoding in encodings:
			# attempt to match each face in the input image to our known
			# encodings
			matches = face_recognition.compare_faces(data["encodings"],
				encoding)
			name = "Unknown" #if face is not recognized, then print Unknown

			# check to see if we have found a match
			if True in matches:
				# find the indexes of all matched faces then initialize a
				# dictionary to count the total number of times each face
				# was matched
				matchedIdxs = [i for (i, b) in enumerate(matches) if b]
				counts = {}

				# loop over the matched indexes and maintain a count for
				# each recognized face face
				for i in matchedIdxs:
					name = data["names"][i]
					counts[name] = counts.get(name, 0) + 1

				# determine the recognized face with the largest number
				# of votes (note: in the event of an unlikely tie Python
				# will select first entry in the dictionary)
				name = max(counts, key=counts.get)

				#If someone in your dataset is identified, print their name on the screen
				if currentname != name:
					currentname = name
					email_to=name
					print(currentname)
					#flash light for 5 seconds
					for x in range(0,2):
						GPIO.output(13,True)
						time.sleep(0.5)
						GPIO.output(13,False)
					# code to mark student attendance
					print("scanning stdents")
					for x in range (0,3):
						frame = vs.read()
						frame = imutils.resize(frame, width=720)
						boxes = face_recognition.face_locations(frame)
						encodings = face_recognition.face_encodings(frame, boxes)
						namesS = []
						for encoding in encodings:
			
							matches = face_recognition.compare_faces(dataS["encodings"],encoding)
							name = "Unknown" 

			
							if True in matches:
								matchedIdxs = [i for (i, b) in enumerate(matches) if b]
								counts = {}
								for i in matchedIdxs:
									name = dataS["names"][i]
									counts[name] = counts.get(name, 0) + 1

				
								name = max(counts, key=counts.get)

				
							if currentname != name:
								currentname = name
								print(currentname)	#for checking only						

							
							namesS.append(name)
							#write to csv file
							#the file is truncated upon each interval and new data is stored.
							# in case of power shortage , system shuts down and the latest attendance is stored but not sent 
							
							f=open(filename,'w',newline='')
							lnwriter=csv.writer(f)
							for name in namesS:
								lnwriter.writerow([name])
						#time to test		
						#time.sleep(1)
						#time for real product
						time.sleep(600) 
						if x==2:
							#send the email from here
							msg=MIMEMultipart()
							msg["From"]=email_from
							msg["To"]=email_to
							msg["Subject"]="The attendance for :"+current_date
							body_email="excel file attached"
							msg.attach(MIMEText(body_email, 'plain'))
							attachment = open(filename , 'rb')
							x = MIMEBase('application', 'octet-stream')
							x.set_payload((attachment).read())
							encoders.encode_base64(x)
							x.add_header('Content-Disposition', "attachment; filename= %s" % filename)
							msg.attach(x)
							s_e = smtplib.SMTP('smtp.gmail.com', 587)
							s_e.starttls()

							s_e.login(email_from,password)
							text = msg.as_string()
							s_e.sendmail(email_from, email_to, text)
							print("Email Sent Successfully")
							over=True
							break
					
				
				names.append(name)

			if over:
				break
				#end the program after sending email
				# update the list of names
				
#part to show video , removed for faster funtioning				
		# # loop over the recognized faces
		# for ((top, right, bottom, left), name) in zip(boxes, names):
		# 	#draw the predicted face name on the image - color is in BGR
		# 	cv2.rectangle(frame, (left, top), (right, bottom),
		# 		(0, 255, 225), 2)
		# 	y = top - 15 if top - 15 > 15 else top + 15
		# 	cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
		# 		.8, (0, 255, 255), 2)

		# # #display the image to our screen
		# cv2.imshow("Facial Recognition is Running", frame)
		#key = cv2.waitKey(1) & 0xFF

		#quit when 'q' key is pressed
		#if key == ord("q")  :
			#break
		
		# update the FPS counter
		#fps.update()
	else:
		GPIO.output(13,False)
		GPIO.output(26,True)
		print("on hold")
		time.sleep(10)
		GPIO.output(26,False)
		key = cv2.waitKey(1) & 0xFF	
		if key == ord("q") :
			break
# stop the timer and display FPS information
GPIO.cleanup()
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
