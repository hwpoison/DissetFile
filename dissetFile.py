import re
import os
import sys
import time

__autor__ = "srbill1996"
__version__ = "0.0.2"

SCRIPT_FILE = {
		"png":{
				'start':b'\x89\x50\x4E\x47',  
				'end':b'\x49\x45\x4E\x44\xAE\x42\x60\x82',
				"script":"""SIGNATURE(start)\nSIGNATURE(end)
				"""
		},
		"bmp":{
				'start':b'\x42\x4D',  
				"script":"""SIGNATURE(start)\nFSEGMENT(2,4, little)
				"""
		},
		"ogg":{
				'start':"no"
		},
		
}
"""Instrucciones:
	SIGNATURE(signature):Detecta una firma en especifico y determina la ubicación dentro del fichero.
	FSEGMENT(x,y, endless_type):Localiza el segment y realiza una suma
"""

def pausa(mensaje="[PAUSA]"):
		input(mensaje)
			
class SegmentProcessor():
	def __init__(self, *args, **kwargs):
		self.DEBUG = True
		self.total_offset_control = 0
		self.instruction_cout = 0
		self.start_offset = 0
		self.end_offset = 0
		
	def dmsg(self, string):
		#Debug message
		if(self.DEBUG):
			print(string)
			
	def takeParams(self, string):
		#Return tuple from string (x,y,..)
		regex = re.findall('\((.*?)\)', string)
		if(',' in string):
			params = [i.strip() for i in regex[0].split(',')]
			#self.dmsg(string + "\nParams: " + str(params))
			return [i for i in params]
		else:
			return regex
	
	def byteBlockProcess(self, bytes_segment):
		#Process Hexadecimal (list)block and return in unique number list
		return [str(hex(bhex))[2:] for bhex in bytes_segment]
		
	def sumHexBlock(self, hex_block):
		#Sum hexadecimal (list)block list and return total sum
		return int("".join(hex_block), 16)
	
	def sumSegment(self, bytes_segment, byte_order=False):
		#take byte segment direct from block and return sum
		segment = self.byteBlockProcess(bytes_segment)
		if(byte_order is 'little_endian'):
			segment.reverse()
		else:
			#is big endian
			pass
		return self.sumHexBlock(segment)
			
	def processInstruction(self, info, file_chunck): 
		#return a slice of indexs start to end if found a coincidence
		actual_instruction = info['script'].split('\n')[self.instruction_cout]
		instruction_args = self.takeParams(actual_instruction)
		real_offset_position = (self.total_offset_control - len(file_chunck))
		if('SIGNATURE' in actual_instruction):
			#Detect start and end of file
			# ~ self.dmsg("Procesando Instruccion SIGNATURE")
			signatureKey = instruction_args[0]
			signature = info[signatureKey]
			if(signature in file_chunck):
				indexSignature = file_chunck.index(signature)
				if(signatureKey == 'start'):
					self.start_offset = indexSignature
					self.dmsg("Firma start %s encontrada en offset %d->%s"%(
							signature, 
							(real_offset_position + self.start_offset), 
							hex(self.start_offset) )
							)
					self.instruction_cout+=1
					return True
				elif(signatureKey == 'end'):
					self.end_offset = indexSignature + len(signature)
					self.dmsg("Firma end %s encontrada en offset %d->%s  "%(
							signature, 
							(real_offset_position + self.end_offset), 
							hex(self.end_offset))
							)
						
					self.instruction_cout+=1
					return slice(self.start_offset, self.end_offset)
				
		elif('FSEGMENT' in actual_instruction):
			self.instruction_cout+=1
			self.dmsg("Procesando Instruccion FSEGMENT")
			block_to_process = file_chunck[int(instruction_args[0]):int(instruction_args[1])+1]
			byteOrder = 'little_endian' if('big_endian' not in instruction_args)\
										else 'big_endian' #Detect Little Endian conversion 
			total_offsets = self.sumSegment(block_to_process, 
											byte_order=byteOrder)
			self.end_offset = total_offsets
			return slice(self.start_offset, self.end_offset)
		return None
				
	def processChunck(self, file_chunck, info, aux_length = 0):
		self.total_offset_control+= aux_length
		for i in range(len(info['script'].split('\n'))):
			process = self.processInstruction(info , file_chunck)
			if(type(process) == slice):
				return process
	
	def reset(self):
		self.start_offset = 0
		self.end_offset = 0
		self.instruction_cout = 0
		
class FileManager():
	def __init__(self, *args, **kargs):
		pass

	def printFileInfo(self, file_name):
		#return File size in MB
		try:
			print("="*30)
			print("Analizyng...")
			print("File Name:%s"%file_name)
			print("File Size:%3.2f MB"%float(os.stat(file_name).st_size/(10**6)))
			print("="*30)
		except(FileNotFoundError):
			print("File not found")
	
	def createDirectory(self, file_path_name):
		#Create directory if not exists
		if(os.path.exists(file_path_name) is not True):
			os.mkdir(file_path_name)
		return file_path_name
			
	def getExtensionFileOfName(self, file_name):
		return file_name.split(".")[1]
		
	def getNameFileOfName(self, file_name):
		return file_name.split(".")[0]
		
	def saveFile(self, file_name,  info):
		#Save file in a new directory with the same name
		with open(file_name, "wb") as saveFile:
			saveFile.write(info)
	
	def openFile(self, file_name):
		try:
			return open(file_name, "rb")
		except(FileNotFoundError):
			print("File not found")
			return False

class FScanner(FileManager):
	def __init__(self, *args, **kargs):
		self.info_files = SCRIPT_FILE
		
	def scanFile(self, file_name, extension=None): 
		file_ = self.openFile(file_name)
		self.printFileInfo(file_name)
		file_extension = self.getExtensionFileOfName(file_name) if extension is None else extension
		file_info = self.info_files[file_extension]

		buffer_ = bytearray()
		total_extract = 0
		process = SegmentProcessor()
		time_start = time.time()
		for chunck in file_:
			buffer_.extend(chunck)
			signature_coincidences = buffer_.count(file_info['start']) 
			for coincidences in range(signature_coincidences ):
				"""Este bucle permite verificar si hay mas de 
					dos firmas en una sola iteracion y analizarlas."""
				result = process.processChunck(
											buffer_, 
											file_info, 
											aux_length =(len(chunck) if coincidences is 0 else 0)
											)
				if(type(result) == slice):
					#save result
					only_file_name = self.getNameFileOfName(file_name)
					file_path = self.createDirectory(only_file_name)
					file_name_ = only_file_name + "_" + str(result.start) + "_" + str(result.stop) 
					file_path = (file_path + "/" ) + (file_name_ + "." + file_extension)
					self.saveFile(file_path, buffer_[result])
					del buffer_[:process.end_offset]
					process.reset()
					total_extract+=1
		print("\n\nTotal files:", total_extract)
		print("Finish in %.1f secs"%(time.time() - time_start))
				

if __name__ == "__main__":
	scan = FScanner()
	scan.scanFile("test_imagenes.png", extension='png')



