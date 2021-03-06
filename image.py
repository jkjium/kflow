import math

#%bucket 64 hilbert #A larger bucket size means more RAM usage and less time rendering.
#image {
#	resolution 1280 959
#	aa 2 2
#	samples 4
#	filter gaussian
#}
#trace-depths {
#	diff 4
#	refl 3
#	refr 2
#}
#gi {
#	type ambocc
#	bright { "sRGB nonlinear" 1 1 1 } 
#	dark { "sRGB nonlinear" 0 0 0 }
#	samples 32
#	maxdist 200.0 
#}
#background {
#	color  { "sRGB nonlinear" 1.0 1.0 1.0 }
#}
#object {
#	shader floor
#	type plane
#	p 0.000000 -11.743686 0.000000
#	n 0 1 0
#}
class Image:
	def __init__(self):
		self.attr = {}
		# attributes for image section
		self.attr['resolution']='1280 959' # to be decided by camera fov
		self.attr['aa'] = '1 2' # 0 1 for preview, 1 2 for final rendering
		self.attr['samples'] = '4' #When used they indirectly affect many aspects of the scene but directly affects DoF and camera/object motion blur.
		self.attr['filter'] = 'gaussian' # box and triangle for preview. gaussian, mitchell, blackman-harris for final
		
		# attributes for trace-depths section
		self.attr['diff']='1'
		self.attr['refl']='4'
		self.attr['refr']='4'
		
		# attributes for gi
		self.attr['type'] = 'ambocc'
		self.attr['bright'] = '{ "sRGB nonlinear" 1 1 1 }'
		self.attr['dark'] = '{ "sRGB nonlinear" 0 0 0 }'
		self.attr['gi:samples']='32'
		self.attr['maxdist']='200.0' # the higher the darker
		
		# background
		self.attr['bg_color'] = '{ "sRGB nonlinear" 1.0 1.0 1.0 }'
		self.attr['floor:color'] = '1.0 1.0 1.0'
		
		# floor
		#self.floorHeight = float('inf') # not support in pymol
		self.floorHeight = 1e3000
		self.attr['floor:p'] = [0.0, 0.0, 0.0] # to be adjust according to the minimum point
		self.attr['floor:n'] = [0.0, 1.0, 0.0] # determined by camera.up attribute
		self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype diffuse\n\tdiff 1.0 1.0 1.0\n}\n'


		# [DOF]
		# works with camera
		# camera.attr['type']='thinlens'
		# camera.fdist = 0 ~ self.maxz #focus distance
		# camera.lensr = 1.0 # blurry value for out of focus objects
		# adjusted in parseCamera()
		# setup values for dof
		# corresponding changes in camera.SCString()

		# dof switch
		self.dof = False
		# fdist for dof
		# updated in checkLowestPoint()
		#self.maxz = -1e3000
		self.maxz = -200
		self.minz = 200

		self.floorShadow = 1
		self.outputWidth = 1280
		self.floorAngle = 90.0

		self.minHeight = 1e3000 #float('inf')
		self.lowestPoint = [0.0, 0.0, 0.0]

		# global shader
		self.attr['globalShader'] = 'diff'


	def setFloorAngle(self, angle):
		self.floorAngle = angle

	def setOutputWidth(self, width):
		self.outputWidth = width

	def setFloorShadow(self, flag):
		self.floorShadow = flag

	def setGlobalShader(self, shader):
		self.attr['globalShader'] = shader

	def setFloorColor(self, color):
		self.attr['floor:color'] = color


	def setFloorShader(self, shader):
		shader=shader.lower()
		if shader == 'diff':
			self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype diffuse\n\tdiff %s\n}\n' % (self.attr['floor:color'])
		elif shader == 'glass':
			self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype glass\n\teta 1.33\n\tcolor  %s\n\tabsorbtion.distance 5.0\n}\n' % (self.attr['floor:color'])
		elif shader == 'mirror':
			self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype mirror\n\trefl %s\n}\n' % (self.attr['floor:color'])
		elif shader == 'shiny':
			self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype shiny\n\tdiff { "sRGB nonlinear" %s }\n\trefl 0.5\n}\n' % (self.attr['floor:color'])
		elif shader == 'phong':
			self.attr['floor:shader'] = 'shader {\n\tname floor\n\ttype phong\n\tdiff { "sRGB linear" %s }\n\tspec { "sRGB linear" %s } 50\n\tsamples 4\n}\n' % (self.attr['floor:color'], self.attr['floor:color'])

	# assume Y is the up axis
	# all the points rotate negative floorAngle to find the lowest height (Y) by applying rotx
	#   old point = [a, b, c]
	#	new point = [a, b*cos(x)+(-1)*c*sin(x), b*sin(x)+c*cos(x)]
	# point in original coordinate system will be recorded
	# minz, maxz are for DOF fdist range
	# this function is called by pov.checkLowestPoint()
	def checkLowestPoint(self, cp):
		np = [cp[0], cp[1]*math.cos(math.radians(-1*self.floorAngle)) + (-1)*cp[2]*math.sin(math.radians(-1*self.floorAngle)), cp[1]*math.sin(math.radians(-1*self.floorAngle)) + cp[2]*math.cos(math.radians(-1*self.floorAngle))]
		if np[1] < self.floorHeight:
			self.floorHeight = np[1]
			self.lowestPoint[0] = cp[0]
			self.lowestPoint[1] = cp[1]
			self.lowestPoint[2] = cp[2]
		if cp[2] > self.maxz:
			self.maxz = cp[2]
		if cp[2] < self.minz:
			self.minz = cp[2]

	# output SC strings
	def SCString(self):
		#image {
		#	resolution 1280 959
		#	aa 2 2
		#	samples 4
		#	filter gaussian
		#}	
		imageStr = 'image {\n\tresolution %s\n\taa %s\n\tsamples %s\n\tfilter %s\n}\n' % (self.attr['resolution'], self.attr['aa'], self.attr['samples'], self.attr['filter'])
		#trace-depths {
		#	diff 4
		#	refl 3
		#	refr 2
		#}
		traceDepthsStr = 'trace-depths {\n\tdiff %s\n\trefl %s\n\trefr %s\n}\n' % (self.attr['diff'], self.attr['refl'], self.attr['refr'])
		#gi {
		#	type ambocc
		#	bright { "sRGB nonlinear" 1 1 1 } 
		#	dark { "sRGB nonlinear" 0 0 0 }
		#	samples 32
		#	maxdist 200.0 
		#}		
		giStr = 'gi {\n\ttype %s\n\tbright %s\n\tdark %s\n\tsamples %s\n\tmaxdist %s\n}\n' % (self.attr['type'], self.attr['bright'], self.attr['dark'], self.attr['gi:samples'], self.attr['maxdist'])
		#background {
		#	color  { "sRGB nonlinear" 1.0 1.0 1.0 }
		#}		
#		bgStr = 'background {\n\tcolor %s\n}' % (self.attr['bg_color'])
		bgStr = 'background {\n\tcolor %s\n}' % ('1.0 1.0 1.0')
		return ('%s\n%s\n%s\n%s\n') % (imageStr, traceDepthsStr, giStr, bgStr)		
	
	def floorSCString(self):
		if self.floorShadow == 0:
			return ''
		else:
		#object {
		#	shader floor
		#	type plane
		#	p 0.000000 -11.743686 0.000000
		#	n 0 1 0
		#}	
			self.attr['floor:n'][1] = math.cos(math.radians(self.floorAngle))
			self.attr['floor:n'][2] = math.sin(math.radians(self.floorAngle))

			self.attr['floor:p'][0] = self.lowestPoint[0]
			self.attr['floor:p'][1] = self.lowestPoint[1] - 2
			self.attr['floor:p'][2] = self.lowestPoint[2]
			return self.attr['floor:shader'] + ('object {\n\tshader floor\n\ttype plane\n\tp %f %f %f\n\tn %f %f %f\n}\n') % (self.attr['floor:p'][0], self.attr['floor:p'][1], self.attr['floor:p'][2], self.attr['floor:n'][0], self.attr['floor:n'][1], self.attr['floor:n'][2])
