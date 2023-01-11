import serial
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import ascii
import time
from Imports.vriCalc import observationManager
import cv2
from astropy.convolution import Gaussian2DKernel,convolve
from scipy.ndimage import gaussian_filter
import matplotlib.image as mpimg
import pickle
import os
import sys
import decawave_ble
import logging
import tenacity
from tqdm import tqdm
myformat = "%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s"

logging.basicConfig(format=myformat,
					level=logging.INFO,
					datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.INFO)

# ToDo. let's try to override tenacity params
decawave_ble.retry_initial_wait = 0.2  # seconds
decawave_ble.retry_num_attempts = 3


def check_total_number_devices(devices):
	number_devices = len(devices)
	logging.info(
		'Found No Decawave devices: Exiting ... nothing to track' if number_devices == 0 else
		'Found {0} Decawave device{1}'.format(number_devices, 's' if number_devices != 1 else '')
	)
	if len(devices) == 0:
		exit(1)
	

def check_total_number_anchors(devices_anchor):
	number_anchors = len(devices_anchor)
	logging.info(
		'Found less than 3 Anchors: Exiting ...' if number_anchors < 3 else
		'Found {0} Decawave Anchor{1}'.format(number_anchors, 's' if number_anchors != 1 else '')
	)
	if number_anchors < 3:
		exit(1)


def check_total_number_tags(devices_tag):
	number_tags = len(devices_tag)
	logging.info(
		'Found No Decawave Tag: Exiting ... nothing to track' if number_tags == 0 else
		'Found {0} Decawave Tag{1}'.format(number_tags, 's' if number_tags != 1 else '')
	)
	if number_tags == 0:
		exit(1)


def create_config_file(ant_pos):
	try:
		with open("./arrays/template_file.txt","r") as hfile,open("./arrays/lego_alma.config","w") as fullfile:
			header = hfile.readlines()
			[fullfile.write(h) for h in header]
			for p in ant_pos:
				fullfile.write(str(p[0])+","+str(p[1])+"\n")
		return True
	except Exception as e:
		print("Error in creating a config file!", e)
		return False
	
logging.info('Scanning for Decawave devices')
devices = decawave_ble.scan_for_decawave_devices()
check_total_number_devices(devices=devices)

# splitting the devices into anchors and tags
# peripherals_xxx comprise {<deviceID>: <current peripheral>} that needs to be updated after a connection was lost
devices_anchor, devices_tag, peripherals_anchor, peripherals_tag = dict(), dict(), dict(), dict()

for key, value in devices.items():
	decawave_peripheral = decawave_ble.get_decawave_peripheral(value)
	operation_mode_data = decawave_ble.get_operation_mode_data_from_peripheral(decawave_peripheral)
	network_id = decawave_ble.get_network_id_from_peripheral(decawave_peripheral)
	# ToDo: a hard-coded network ID is not a good idea! We need a tiny application that can re-assign
	#  devices with any deviceID to a specific network ID to retrieve one that went astray or was hijacked.
	if network_id == 0x66ce:
		if operation_mode_data['device_type_name'] == 'Tag':
			devices_tag[key] = value
			peripherals_tag[key] = decawave_peripheral
		elif operation_mode_data['device_type_name'] == 'Anchor':
			devices_anchor[key] = value
			peripherals_anchor[key] = decawave_peripheral
	else:
		logging.warning("Decawave devices found from network ID: {}, being disregarded".format(network_id))
# anchors
check_total_number_anchors(devices_anchor=devices_anchor)
# and print their positions
for key, decawave_peripheral in peripherals_anchor.items():
	location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
	print({key: location_data["position_data"]})
# tags
check_total_number_tags(devices_tag=devices_tag)
for key, decawave_peripheral in peripherals_anchor.items():
	location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
	print({key: location_data["position_data"]})
 # tags
check_total_number_tags(devices_tag=devices_tag)
number_tags = len(devices_tag)
#given 3 tag positions at 3 known alma coord pads, transform tag position to alma coords
def get_transform(x1,x2,x3):
	try:
		X12 = np.array([x1,x2]).T
		X23 = np.array([x2,x3]).T
		Y12 = np.array([[-157.5,-96],[159,-145.5]]).T
		Y23 = np.array([[159,-145.5],[10.5,30.]]).T
		A = np.matmul((Y12-Y23),np.linalg.inv(X12-X23))
		B = Y12 - np.matmul(A,X12)
		return A,B.T[0]
	except Exception as e:
		print("can't get matrix transform:",e)
		return None

def get_pos_tag(tag_id,verbose = False):
	while True:
		for key, decawave_peripheral in peripherals_tag.items():
			if key == tag_id:
				try:
					location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
					if verbose:
						print({key: location_data["position_data"]})
					x = location_data["position_data"]['x_position']
					y = location_data["position_data"]['y_position']
					z = location_data["position_data"]['z_position']
					return np.array([x,y,z])
				except tenacity.RetryError:
					print("Device {} disconnected: fetch peripheral again".format(key))
					# check if the device is still accessable, if not resume and retry next time
					try:
						decawave_peripheral = decawave_ble.get_decawave_peripheral(devices_tag[key])
						peripherals_tag[key] = decawave_peripheral
					except tenacity.RetryError:
						print("Device {} unable to reconnect, retrying ...".format(key))
		
				except Exception as e:
					print("Other Exception: {}".format(e))
					return None
def get_pos_tags(verbose = False):
	keypos = {}
	while len(keypos) < number_tags:
		for key, decawave_peripheral in peripherals_tag.items():
			try:
				location_data = decawave_ble.get_location_data_from_peripheral(decawave_peripheral)
				if verbose:
					print({key: location_data["position_data"]})
				keypos[key] = location_data["position_data"]
			except tenacity.RetryError:
				print("Device {} disconnected: fetch peripheral again".format(key))
				# check if the device is still accessable, if not resume and retry next time
				try:
					decawave_peripheral = decawave_ble.get_decawave_peripheral(devices_tag[key])
					peripherals_tag[key] = decawave_peripheral
				except tenacity.RetryError:
					print("Device {} unable to reconnect, retrying ...".format(key))
		
			except Exception as e:
				print("Other Exception: {}".format(e))
				return None
	return keypos
def apply_transform(A,b):
	tag_pos_dict = get_pos_tags()
	trans_pos_dict = {}
	for key in tag_pos_dict.keys():
		trans_pos_dict[key]=A@np.array([tag_pos_dict[key]['x_position'],tag_pos_dict[key]['y_position']]) + b
	return trans_pos_dict
def get_3pos_tag(tag_id):
	X_vecs = []
	print("Aligning tags with ALMA")
	for ii in ['red','orange','green']:
		input("Place tag "+tag_id+" at the "+ (ii) +" pad and press Enter")
		temp_vec = []
		with tqdm(total = 40,desc="Collecting position data", unit="tag positions") as pbar:
			while len(temp_vec) < 40:
				data_in = get_pos_tag(tag_id)[:-1]
				if data_in is not None:
					temp_vec.append(data_in)
					pbar.update(1)
		temp_vec = np.median(temp_vec,axis=0)
		X_vecs.append(temp_vec)
	print(X_vecs)
	return X_vecs

#os.chdir("/home/dpg-physik/Downloads/friendlyVRI-master")


print(os.getcwd())
ans = input("Perform tag to ALMA position calibration?(y) load from disk? (l) don't use tags! (n)")
if ans == "y":
	x1,x2,x3 = get_3pos_tag('DW5293')
	A,b = get_transform(x1,x2,x3)
	with open("transM.pickle",'wb') as fout:
		pickle.dump([A,b],fout)
	vlbi = True
elif ans == "l":
	try: 
		with open("transM.pickle",'rb') as fin:
			A,b = pickle.load(fin)
		vlbi = True
	except Exception as e:
		print(e,"File not loaded!")
		vlbi = False
elif ans == "n":
	vlbi = False

	

LOOP_TIME = 0.5 #seconds
SCALE_ARRAY =3.
HA_START = -2.
HA_END = +2. 
FREQ = 3e5 #MHz
DEC = -40 #declination
PIX_SCALE = 0.05 #arcseconds
webcam = False
IMAGEFILE = "models/toma4_crop.png"
HA  = 0
INT_T = 2
PAUSE_CONDITION = False
SGAL_BIT = 4
M51_BIT = 6
HA_M6_BIT = 1
HA_P6_BIT = 3
HA_0_BIT = 2
CAM_BIT = 5
FULLTRK_BIT = 7
ZOOM = 24
try:
	ant_bits = ascii.read("ant_pos.txt")
	ant_dict = dict(zip(ant_bits['bit'],zip(ant_bits['posx'],ant_bits['posy'])))
except Exception as e:
	print(e)

try:
	ser = serial.Serial('/dev/ttyUSB0',19200,timeout = 1,parity  = serial.PARITY_NONE,rtscts=False)
	ser2 = serial.Serial('/dev/ttyUSB1',19200,timeout = 1,parity  = serial.PARITY_NONE,rtscts=False)
	ser.write('b\r'.encode())
	linein = ser.readline()
	bit_pos = np.where(np.array([bit == '1' for bit in linein]) == True)[0]
	
	ser2.write('b\r'.encode())
	linein = ser2.readline()
	bit_pos2 = np.where(np.array([bit == '1' for bit in linein]) == True)[0]

	while len(bit_pos2) < 6 and len(bit_pos) < 6:
		input("Press Enter when you have placed at least 6 antennae on pads")
		ser.write('b\r'.encode())
		linein = ser.readline()
		bit_pos = np.where(np.array([bit == '1' for bit in linein.decode('utf-8')]) == True)[0]
		print(bit_pos)	
		ser2.write('b\r'.encode())
		linein = ser2.readline()
		bit_pos2 = np.where(np.array([bit == '1' for bit in linein.decode('utf-8')]) == True)[0]
		print(bit_pos2)
		print(len(bit_pos))
		print(len(bit_pos2))



	if len(bit_pos2) >= 6:
		ser = serial.Serial('/dev/ttyUSB1',19200,timeout = 1,parity  = serial.PARITY_NONE,rtscts=False)
		ser2 = serial.Serial('/dev/ttyUSB0',19200,timeout = 1,parity  = serial.PARITY_NONE,rtscts=False)

#	if ser.isOpen() and ser2.isOpen(): break
except Exception as e:
	print("Error in connecting to port!",e)

#ii= 0
#jj=0
plt.ion()
plt.style.use('dark_background')
while True:
	#	HA_START = HA - 0.5
#	HA_END = HA + 0.5
#	HA+=1
	#if HA > 6: 
#		HA = -6
#		HA_START = -6
#		HA_END = 6
	#FREQ += 1000
	#if FREQ >= 3e4: FREQ = 5e3
	try:
		print("start")
		obsMan = observationManager(verbose=True, debug=True)
		obsMan.get_available_arrays()
		## ask the box for the antenna configuration:
		if not ser.isOpen(): 
			print("Port 1 closed!")
			break
		
		ser.write('b\r'.encode())
		linein = ser.readline()
		bit_pos = np.where(np.array([bit == '1' for bit in linein.decode('utf-8')]) == True)[0]
		#bit_pos = ant_dict.keys()	
		print(linein)
		print(bit_pos,len(bit_pos))

		##ask for the button config
		if not ser2.isOpen(): 
			print("Port 2 closed!")
			break
		ser2.write('b\r'.encode())
		linein2 = ser2.readline()
		bit_pos2 = np.where(np.array([bit == '1' for bit in linein2.decode('utf-8')]) == True)[0]
				
		print(linein2)
		print(bit_pos2,len(bit_pos2))
		
		print("A")
		if not(int(linein2[HA_M6_BIT])) and not(int(linein2[HA_0_BIT])) and not(int(linein2[HA_P6_BIT])):
			PAUSE_CONDITION = True 
			print("PAUSE TRUE")
			#continue
		else:
			print("PAUSE FALSE")
			PAUSE_CONDITION = False
		webcam = False
		print("B")
		PIX_SCALE = 0.05
		if linein2[SGAL_BIT] == '0':
			IMAGEFILE = "models/toma4_crop.png"
		elif linein2[M51_BIT] == '0':
			IMAGEFILE = "models/M51.png"
		elif linein2[CAM_BIT] == '0':
			IMAGEFILE = "models/webcam.png"
			PIX_SCALE = 0.1
			webcam = True
		print(IMAGEFILE)
		if linein2[SGAL_BIT] == '0' and  linein2[CAM_BIT] == '0' and  linein2[M51_BIT] == '0':
			IMAGEFILE = "models/marilyn-einstein.png"
			PIX_SCALE = 0.1

		if linein2[SGAL_BIT] == '1' and  linein2[M51_BIT] == '1' and linein2[CAM_BIT] == '1':
			IMAGEFILE= "models/mistery_med.png"
				
		if linein2[FULLTRK_BIT] == '1':
			INT_T = 2
			if linein2[HA_0_BIT] == '1':
				HA = 0 
			elif linein2[HA_M6_BIT] == '1':
				HA = -5
			elif linein2[HA_P6_BIT] == '1':
				HA = +5
		else:

			INT_T = 12
			HA = 0

		
		HA_START = HA - INT_T*0.5
		HA_END = HA + INT_T*0.5
		print(IMAGEFILE, INT_T,HA_START,HA_END,PAUSE_CONDITION,"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
		   


		ant_pos = np.array([np.array(ant_dict[bb])*SCALE_ARRAY for bb in bit_pos])#multiply with a factor, default 13 to scale up the array baselines
		if vlbi:
			trans_pos_dict = apply_transform(A,b)
			for key in trans_pos_dict.keys():
				ant_pos = np.concatenate([ant_pos,[np.array([trans_pos_dict[key][0],trans_pos_dict[key][1]])]])

		print("ant_pos_var:",ant_pos)		
		if len(ant_pos) == 0: #if there's just one antenna left, there's nothing to show 
			continue
		elif len(ant_pos) > 1: 
			xx_antpos,yy_antpos = ant_pos.T
			create_config_file(ant_pos)
			PLOT = True
			SINGLEDISH = False
		else: 
			xx_antpos,yy_antpos = ant_pos.T
			PLOT = True	
			SINGLEDISH = True
			
		
		# Select array configurations and hour-angle ranges.
		obsMan.select_array('LEGOALMA_Cycle6-C43-9',haStart = HA_START,haEnd = HA_END,sampRate_s=300)
		#obsMan.select_array('ALMA_Cycle6-C43-1',haStart = HA_START,haEnd = HA_END,sampRate_s=300)
		obsMan.get_selected_arrays()
		# Set the observing frequency (MHz) and source declination (deg).
		obsMan.set_obs_parms(FREQ, DEC)
		
		# Calculate the uv-coverage
		obsMan.calc_uvcoverage()
		
		if webcam:
			try:
				cam = cv2.VideoCapture()
				cam.open(0)
				for i in range(10):
					success, img = cam.read()
				cam.release()
				print('SAHAPE',np.shape(img))
				if success:
					cv2.imwrite("models/webcam.png", img[0:480,80:560])
					obsMan.load_model_image(IMAGEFILE)
					obsMan.set_pixscale(PIX_SCALE)
					
			except Exception as e:
				print(e)
				pass
	
	
	
		else:
			obsMan.load_model_image(IMAGEFILE)
			obsMan.set_pixscale(PIX_SCALE)
	
	
		if PLOT:
			print(IMAGEFILE)	
			try:
				# Calculate the FFT of the model image
				obsMan.invert_model()
				if not SINGLEDISH:	
					# Grid the uv-coverage onto the same pixels as the FFT as the model image
					obsMan.grid_uvcoverage()
					
					# Create the beam image
					obsMan.calc_beam()
					
					# Apply the uv-coverage and create observed image
					obsMan.invert_observation()
		
				plt.clf()

				plogo = plt.subplot(111)
				imglogo=mpimg.imread('models/aifa-logo.png')				
				plogo.imshow(imglogo)
				plogo.set_position([0.0,0.0,0.1,0.1],which='both')
				plogo.axes.get_xaxis().set_visible(False)
				plogo.axes.get_yaxis().set_visible(False)


				#plto antenna position
				p0 = plt.subplot(2,4,1)
				p0.set_title("ALMA von oben",fontsize = 15)
				p0.scatter(xx_antpos,yy_antpos)
				zoom_factor = 1.
				if max(xx_antpos) > 250 or min(xx_antpos) < -250 or max(yy_antpos) > 250 or min(yy_antpos) < -250:
					x_zoom_factor = 1.
					y_zoom_factor = 1.
					x_over_max = abs(max(xx_antpos)/250)
					x_under_min = abs(min(xx_antpos)/250)
					y_over_max = abs(max(yy_antpos)/250)
					y_under_min = abs(min(yy_antpos)/250)
					x_max = max(x_over_max,x_under_min)
					if x_max > 1:
						x_zoom_factor = x_max
					y_max = max(y_over_max,y_under_min)
					if y_max > 1:
						y_zoom_factor = y_max
					zoom_factor = max(y_zoom_factor,x_zoom_factor)
					pass

				else:
					p0.set_xlim(-250,250)
					p0.set_ylim(-250,250)
				p0.set_xlabel("Meters")
				p0.set_ylabel("Meters")
				p0.set_aspect('equal')
				print("zoomfactor and zoom: ",zoom_factor,ZOOM)
				
				
				pp0 = plt.subplot(2,4,5)
				pp0.set_title("ALMA aus Perspektive der Quelle",fontsize = 15)
				pp0.text(4.5,-0.3,r"Powered by: Friendly VRI C.R. Purcell R. Truelove",ha='center', va='center',fontsize =8, transform=pp0.transAxes)
				
				hrangle_rad = np.radians(HA*15)
				dec_rad = np.radians(DEC)
				xx_earth_cen = -yy_antpos*np.sin(np.radians(-23.023))
				yy_earth_cen = xx_antpos
				zz_earth_cen = yy_antpos*np.cos(np.radians(-23.023))
			
				xx_antpos_proj = -(xx_earth_cen*np.sin(hrangle_rad)+yy_earth_cen*np.cos(hrangle_rad))
				yy_antpos_proj = -xx_earth_cen*np.sin(dec_rad)*np.cos(hrangle_rad) + yy_earth_cen*np.sin(dec_rad)*np.sin(hrangle_rad)+zz_earth_cen*np.cos(dec_rad)

				

				if HA > 0:
					pp0.scatter(yy_antpos_proj,xx_antpos_proj)
				elif HA < 0:
					pp0.scatter(-yy_antpos_proj,-xx_antpos_proj)
				elif HA == 0:
					pp0.scatter(xx_antpos_proj,-yy_antpos_proj)
					
				if max(xx_antpos) > 250 or min(xx_antpos) < -250 or max(yy_antpos) > 250 or min(yy_antpos) < -250:
								pass
					
				else:
					p0.set_xlim(-250,250)
					p0.set_ylim(-250,250)
					pp0.set_xlim(-250,250)
					pp0.set_ylim(-250,250)
				pp0.set_aspect('equal')
				pp0.set_xlabel("<<Meters>>")
				pp0.set_ylabel("<<Meters>>")



				#plot original image
				p1 = plt.subplot(2,4,2)
				if IMAGEFILE == "models/mistery_med.png":
					qmarkimg=mpimg.imread('models/mistery_qmark.png')				
					p1.imshow(qmarkimg,cmap = 'gist_heat')
				else:
					p1.imshow(np.real(obsMan.modelImgArr),origin = 'lower',cmap = 'gist_heat')
				p1.axes.get_xaxis().set_visible(False)
				p1.axes.get_yaxis().set_visible(False)
				p1.set_title("Reales Bild der Quelle",fontsize = 15)
			
				if not SINGLEDISH:

					#plot synthbeam
					p2 = plt.subplot(2,4,3)
					xlims,ylims = np.real(obsMan.beamArr).shape
					p2.imshow(np.real(obsMan.beamArr),origin = 'lower',cmap = 'gist_heat')
					p2.set_xlim(xlims/2 - xlims/2/zoom_factor,xlims/2 + xlims/2/zoom_factor)
					p2.set_ylim(ylims/2 - ylims/2/zoom_factor,ylims/2 + ylims/2/zoom_factor)
					p2.text(-0.1,0.5,r"$\bigotimes$",ha='center', va='center',fontsize = 25, transform=p2.transAxes)
					p2.axes.get_xaxis().set_visible(False)
					p2.axes.get_yaxis().set_visible(False)
					p2.set_title("ALMAs Bild einer Punktquelle",fontsize = 15)
		
					#plot final image
					p3 = plt.subplot(2,4,4)
					p3.imshow(np.real(obsMan.obsImgArr),origin='lower',cmap='gist_heat')
					p3.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 25, transform=p3.transAxes)
					p3.axes.get_xaxis().set_visible(False)
					p3.axes.get_yaxis().set_visible(False)
					p3.set_title("ALMAs Bild der Quelle",fontsize = 15)
					
			
				else:
					if not webcam:
						print("SINGLEDISH")
						#plot different final image, no beam
						with open(IMAGEFILE.split(".")[0]+"_SDOUT.pickle",'rb') as fin:
							simage_sd = pickle.load(fin) 
						#sgdish_image = gaussian_filter(obsMan.modelImgArr,133,mode = 'constant')
						p3 = plt.subplot(2,4,4)
						p3.imshow(simage_sd,origin = 'lower',cmap = 'gist_heat')
						p3.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 25, transform=p3.transAxes)
						p3.axes.get_xaxis().set_visible(False)
						p3.axes.get_yaxis().set_visible(False)
						p3.set_title("Single Dish View",fontsize = 15)
	
	
		
				#fft of original image
				
				p4 = plt.subplot(2,4,6)
				mm,ll = np.shape(obsMan.modelFFTarr)
				#p4.imshow(np.log10(abs(obsMan.modelFFTarr)),cmap = 'gist_heat',interpolation = 'bicubic')
				p4.imshow(np.log10(abs(obsMan.modelFFTarr)),cmap = 'gist_heat',interpolation = 'bicubic')
				p4.set_xlim(ll/2-ll/ZOOM*zoom_factor,ll/2+ll/ZOOM*zoom_factor)
				p4.set_ylim(mm/2-mm/ZOOM*zoom_factor,mm/2+mm/ZOOM*zoom_factor)
				p4.axes.get_xaxis().set_visible(False)
				p4.axes.get_yaxis().set_visible(False)
				p4.set_title("Fouriertransformierte Quelle",fontsize = 15)
			
			
				if not SINGLEDISH:	
					#plot uvcoverage
					p5 = plt.subplot(2,4,7)
					p5.scatter(obsMan.arrsSelected[0]['uArr_lam'],obsMan.arrsSelected[0]['vArr_lam'],s=1)
					p5.scatter(-1.*obsMan.arrsSelected[0]['uArr_lam'],-1*obsMan.arrsSelected[0]['vArr_lam'],s=1)
					p5.set_xlim(obsMan.pixScaleFFTX_lam*(-ll/ZOOM*zoom_factor),(obsMan.pixScaleFFTX_lam*(+ll/ZOOM*zoom_factor)))
					p5.set_ylim(obsMan.pixScaleFFTY_lam*(-mm/ZOOM*zoom_factor),(obsMan.pixScaleFFTY_lam*(+mm/ZOOM*zoom_factor)))
					p5.set_aspect(p4.get_aspect())
					p5.text(-0.1,0.5,r"$\times$",ha='center', va='center',fontsize = 20, transform=p5.transAxes)
					p5.axes.get_xaxis().set_visible(False)
					p5.axes.get_yaxis().set_visible(False)
					p5.set_title("Abdeckung der Fourierebene",fontsize = 15)
		
					
					#fft of final image
					p6 = plt.subplot(2,4,8)
					p6.imshow(np.log10(abs(obsMan.obsFFTarr)+1e3)-3,cmap = 'gist_heat',interpolation = 'bicubic')
					p6.set_xlim(ll/2-ll/ZOOM*zoom_factor,ll/2+ll/ZOOM*zoom_factor)
					p6.set_ylim(mm/2-mm/ZOOM*zoom_factor,mm/2+mm/ZOOM*zoom_factor)
					p6.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 20, transform=p6.transAxes)
					p6.set_aspect('equal')
					p6.axes.get_xaxis().set_visible(False)
					p6.axes.get_yaxis().set_visible(False)
					p6.set_title("Fouriertransformiertes Bild\n der Quelle",fontsize = 15)
					
	
				
				plt.show()	
			except Exception as e:
				print(e)
				pass
	
		else:
			pass #we should plot that something's wrong and you can't have one antenna or no antenna...
	
		#plt.clf()
		#pl = plt.subplot(111)
		#kernel = Gaussian2DKernel(131,x_size = 4*130+1,y_size = 4*130+1)
		#sgdish_image = convolve(obsMan.modelImgArr,kernel,boundary = 'extend')

		#with open(IMAGEFILE.split(".")[0]+"_SDOUT"+"."+ IMAGEFILE.split(".")[1],"wb") as fout:
		#	pickle.dump(sgdish_image,fout)
		#pl.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 20, transform=pl.transAxes)
		#pl.axes.get_xaxis().set_visible(False)
		#pl.axes.get_yaxis().set_visible(False)
		#pl.set_title("ALMA's view "+"{:.2e}".format(FREQ),fontsize = 20)
		#pl.imshow(sgdish_image,origin='lower',cmap='gist_heat')
		#plt.savefig(IMAGEFILE.split(".")[0]+"_almaview_saved_SD"+"."+ IMAGEFILE.split(".")[1])

		plt.pause(LOOP_TIME)
		print(ant_pos)
	except KeyboardInterrupt:
		plt.clf()
		pl = plt.subplot(111)
		pl.imshow(np.real(obsMan.modelImgArr),origin='lower',cmap='gist_heat')
#		pl.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 20, transform=pl.transAxes)
		pl.axes.get_xaxis().set_visible(False)
		pl.axes.get_yaxis().set_visible(False)
#		pl.set_title("ALMA's view "+"{:.2e}".fo.decode('utf-8')rmat(FREQ),fontsize = 20)
		plt.savefig(IMAGEFILE.split(".")[0]+"_almaview_saved"+"."+ IMAGEFILE.split(".")[1])

		#if SINGLEDISH:	
		#	plt.clf()
		#	pl = plt.subplot(111)
		#	kernel = Gaussian2DKernel(130,x_size = 4*130,y_size = 4*130)
		#	sgdish_image = convolve(obsMan.modelImgArr,kernel,boundary = 'extend')
		#	pl.imshow(sgdish_image,origin='lower',cmap='gist_heat')
		#	pl.text(-0.1,0.5,r"$=$",ha='center', va='center',fontsize = 20, transform=pl.transAxes)
		#	pl.axes.get_xaxis().set_visible(False)
		#	pl.axes.get_yaxis().set_visible(False)
		#	pl.set_title("ALMA's view "+"{:.2e}".format(FREQ),fontsize = 20)
		#	plt.savefig(IMAGEFILE.split(".")[0]+"_almaview_saved_SD"+"."+ IMAGEFILE.split(".")[1])


		break
cam.release()
plt.close()
ser.close()
