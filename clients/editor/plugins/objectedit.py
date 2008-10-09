#!/usr/bin/env python
# coding: utf-8
# ###################################################
# Copyright (C) 2008 The Zero-Projekt team
# http://zero-projekt.net
# info@zero-projekt.net
# This file is part of Zero "Was vom Morgen blieb"
#
# The Zero-Projekt codebase is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import fife
import plugin
import pychan
import pychan.widgets as widgets
from pychan.tools import callbackWithArguments as cbwa

import settings as Settings

class ObjectEdit(plugin.Plugin):
	def __init__(self, engine, mapedit):
		"""
			ObjectEdit plugin for FIFEdit
			
			Mission: provide a gui mask to edit all important object data within the editor
			(id, offsets, rotation, blocking, static)
			
			namespaces and object ids are excluded
			
			Current features:
				- click instance and get all known data
				- edit offsets, rotation, blocking, static
				- outline highlighting of the selected object
				- 3 data states: current, previous and default (so there is at least a one-step-undo)
				
			Missing features:
				- object saving
				- id saving (handled by Fifedit via save map, but we have to set the id from here)
				- a lot of bug fixing concerning the rotation and the data records ^^
				- cleanup
		
			NOTE:
				- this tool isn't ready for a working enviroment (yet)
		"""
		# Fifedit plugin data
		self.menu_items = { 'ObjectEdit' : self.toggle_offsetedit }
		
		self._mapedit = mapedit

# FIXME		
		# this is _very bad_ - but I need to change the current rotation code by providing
		# project specific rotation angles. FIFE later should provide a list of the loaded
		# object rotations (they are provided by the xml files, so we just need to use them...)
		self._mapedit._objectedit_rotations = None
# end FIXME		
		self.active = False
		
		self.imagepool = engine.getImagePool()
		self.animationpool = engine.getAnimationPool()
			
		self._camera = None
		self._layer = None
		
		self.guidata = {}
		self.objectdata = {}

		self._reset()		
		self.create_gui()

	
	def _reset(self):
		"""
			resets all dynamic vars, but leaves out static ones (e.g. camera, layer)

		"""
		self._instances = None
		self._image = None
		self._animation = False
		self._rotation = None
		self._avail_rotations = []
		self._namespace = None	
		self._blocking = 0
		self._static = 0
		self._object_id = None	
		self._instance_id = None
		self._fixed_rotation = None
		
		self.guidata['instance_id'] = 'None'
		self.guidata['object_id'] = 'None'
		self.guidata['x_offset'] = 0
		self.guidata['y_offset'] = 0
		self.guidata['instance_rotation'] = 0
		self.guidata['namespace'] = 'None'
		self.guidata['blocking'] = 0
		self.guidata['static'] = 0
		
		if self._camera is not None:
			self.renderer.removeAllOutlines()		
		
	def create_gui(self):
		"""
			- creates the gui skeleton by loading the xml file
			- finds some important childs and saves their widget in the object
		"""
		self.container = pychan.loadXML('gui/offsetedit.xml')
		self.container.mapEvents({
			'x_offset_up' 	: cbwa(self.change_offset_x, 1),
			'x_offset_dn' 	: cbwa(self.change_offset_x, -1),
			
			'y_offset_up' 	: cbwa(self.change_offset_y, 1),
			'y_offset_dn' 	: cbwa(self.change_offset_y, -1),
			
			'use_data'		: cbwa(self.use_user_data),
			'previous_data' : cbwa(self.load_previous_data),
			'default_data'	: cbwa(self.load_default_data)
		})

		self._gui_anim_panel_wrapper = self.container.findChild(name="animation_panel_wrapper")
		self._gui_anim_panel = self._gui_anim_panel_wrapper.findChild(name="animation_panel")
		
		self._gui_anim_panel_wrapper.removeChild(self._gui_anim_panel)

		self._gui_rotation_dropdown = self.container.findChild(name="select_rotations")
		
		self._gui_xoffset_textfield = self.container.findChild(name="x_offset")
		self._gui_yoffset_textfield = self.container.findChild(name="y_offset")

	def _get_gui_size(self):
		"""
			gets the current size of the gui window and calculates new position
			(atm top right corner)
		"""
		size = self.container._getSize()
		self.position = ((Settings.ScreenWidth - 10 - size[0]), 10)
		
	def update_gui(self):
		"""
			updates the gui widgets with current instance data
			
			FIXME: 
				- drop animation support or turn it into something useful
		"""
		#if self._animation is False:
			#try:
				#self._gui_anim_panel_wrapper.removeChild(self._gui_anim_panel)
			#except:
				#pass
		#elif self._animation is True:
			#try:
				#self._gui_anim_panel_wrapper.resizeToContent()				
				#self._gui_anim_panel_wrapper.addChild(self._gui_anim_panel)
				#self._gui_anim_panel_wrapper.resizeToContent()
			#except:
				#pass
		
		self.container.distributeInitialData({
			'select_rotations' 	: self._avail_rotations,
			'instance_id'		: self.guidata['instance_id'],
			'object_id'			: self.guidata['object_id'],
			'x_offset'			: self.guidata['x_offset'],
			'y_offset'			: self.guidata['y_offset'],
			'instance_rotation' : self.guidata['instance_rotation'],
			'object_namespace'	: self.guidata['namespace'],
			'object_blocking'	: self.guidata['blocking'],
			'object_static'		: self.guidata['static'],
		})
		try:
			print self._avail_rotations
			print self._fixed_rotation
			index = self._avail_rotations.index( str(self._fixed_rotation) )
			self._gui_rotation_dropdown._setSelected(index)
		except:
#			pass
			print "Angle (", self._fixed_rotation, ") not supported by this instance"
		
	def toggle_gui(self):
		"""
			show / hide the gui
			
			FIXME:
				- ATM not in use, needs some additional code when showing / hiding the gui (see input() )
		"""
		if self.container.isVisible():
			self.container.hide()
		else:
			self.container.show()
			
	def toggle_offsetedit(self):
		"""
			- toggles the object editor activ / inactiv - just in case the user don't want to have
			  the gui popping up all the time while mapping :-)
			- hides gui
		"""
		if self.active is True:
			self.active = False
			if self.container.isVisible():
				self.container.hide()
		else:
			self.active = True	

	def highlight_selected_instance(self):
		"""
			just highlights selected instance
		"""
		self.renderer.removeAllOutlines() 
		self.renderer.addOutlined(self._instances[0], 205, 205, 205, 1)
			
	def change_offset_x(self, value=1):
		"""
			- callback for changing x offset
			- changes x offset of current instance (image)
			- updates gui
			
			@param	int		value	the modifier for the x offset
		"""		
		if self._image is not None:
			self._image.setXShift(self._image.getXShift() + value)
			
			self.guidata['x_offset'] = str( self._image.getXShift() )
			self.update_gui()

	def change_offset_y(self, value=1):
		"""
			- callback for changing y offset
			- changes y offset of current instance (image)
			- updates gui
			
			@param	int		value	the modifier for the y offset
		"""
		if self._image is not None:
			self._image.setYShift(self._image.getYShift() + value)
			
			self.guidata['y_offset'] = str( self._image.getYShift() )
			self.update_gui()

	def use_user_data(self):
		"""
			- takes the users values and applies them directly to the current ._instance
			- writes current data record
			- writes previous data record
			- updates gui
		
			FIXME:
			- parse user data in case user think strings are considered to be integer offset values...
		"""
		xoffset = self._gui_xoffset_textfield._getText()
		yoffset = self._gui_yoffset_textfield._getText()
		
		# workaround - dropdown list only has 2 entries, but sends 3 -> pychan bug?
		if len(self._avail_rotations) < self._gui_rotation_dropdown._getSelected():
			index = len(self._avail_rotations)
		else:
			index = self._gui_rotation_dropdown._getSelected()
		
		# strange, but this helps to rotate the image correctly to the value the user selected
		angle = int( self._avail_rotations[index] )
		angle = int(angle - abs( self._camera.getTilt() ) )
		if angle == 360:
			angle = 0
		
		self._instances[0].setRotation(angle)
		self.get_instance_data(None, None, angle)
		
		try:
			self._image.setXShift( int(xoffset) )
		except:
			pass
#		print "x offset must me of type int!"
		try:
			self._image.setYShift( int(yoffset) )
		except:
			pass
#		print "y offset must be of type int!"
		
		self.write_current_data()
		self.objectdata[self._namespace][self._object_id]['previous'] = self.objectdata[self._namespace][self._object_id]['current'].copy()
		self.update_gui()
		
	def load_previous_data(self):
		"""
			- writes a copy of the previous record back to the current record (aka one-step-undo)
			- loads current data into class object
			- updates gui
		"""
		self.objectdata[self._namespace][self._object_id]['current'] = self.objectdata[self._namespace][self._object_id]['previous'].copy()
		self.load_current_data()
		self.update_gui()
		
	def load_default_data(self):
		"""
			- writes a copy of the default record back to the current record
			- loads current data into class object
			- updates gui			
		"""
		self.objectdata[self._namespace][self._object_id]['current'] = self.objectdata[self._namespace][self._object_id]['default'].copy()
		self.load_current_data()
		self.update_gui()

	def load_current_data(self):
		"""
			loads the current record into class object
		"""
		self._image = self.objectdata[self._namespace][self._object_id]['current']['image']
		self._animation = self.objectdata[self._namespace][self._object_id]['current']['animation']
		self._rotation = self.objectdata[self._namespace][self._object_id]['current']['rotation']
		self._fixed_rotation = self.objectdata[self._namespace][self._object_id]['current']['fixed_rotation']
		self._avail_rotations = self.objectdata[self._namespace][self._object_id]['current']['avail_rotations']
		self._blocking = self.objectdata[self._namespace][self._object_id]['current']['blocking']
		self._static = self.objectdata[self._namespace][self._object_id]['current']['static']
		self._instance_id = self.objectdata[self._namespace][self._object_id]['current']['instance_id']
		self._image.setXShift( self.objectdata[self._namespace][self._object_id]['current']['xoffset'] )
		self._image.setYShift( self.objectdata[self._namespace][self._object_id]['current']['yoffset'] )
		
		self.write_current_guidata()
		
	def write_current_data(self):
		"""
			updates the current record
		"""
		self.objectdata[self._namespace][self._object_id]['current']['instance'] = self._instances[0]
		self.objectdata[self._namespace][self._object_id]['current']['image'] = self._image
		self.objectdata[self._namespace][self._object_id]['current']['animation'] = self._animation
		self.objectdata[self._namespace][self._object_id]['current']['rotation'] = self._rotation
		self.objectdata[self._namespace][self._object_id]['current']['fixed_rotation'] = self._fixed_rotation
		self.objectdata[self._namespace][self._object_id]['current']['avail_rotations'] = self._avail_rotations
		self.objectdata[self._namespace][self._object_id]['current']['blocking'] = self._blocking
		self.objectdata[self._namespace][self._object_id]['current']['static'] = self._static
		self.objectdata[self._namespace][self._object_id]['current']['instance_id'] = self._instance_id
		self.objectdata[self._namespace][self._object_id]['current']['xoffset'] = self._image.getXShift()
		self.objectdata[self._namespace][self._object_id]['current']['yoffset'] = self._image.getYShift()
		
		self.write_current_guidata()
		
	def write_current_guidata(self):
		"""
			updates the gui data with
		"""		
		self.guidata['instance_rotation'] = str( self._instances[0].getRotation() )		
		self.guidata['object_id'] = str( self._object_id )
		self.guidata['instance_id'] = str( self._instance_id )
		self.guidata['x_offset'] = str( self._image.getXShift() )
		self.guidata['y_offset'] = str( self._image.getYShift() )
		self.guidata['namespace'] = self._namespace	
		self.guidata['blocking'] = str( self._blocking )
		self.guidata['static'] = str( self._static )		
			
	def get_instance_data(self, timestamp=None, frame=None, angle=-1, instance=None):
		"""
			- grabs all available data from both object and instance
			- checks if we already hold a record (namespace + object id)
			
			FIXME:
				1.) we need to fix the instance rotation / rotation issue
				2.) use correct instance rotations to store data for _each_ available rotation
				3.) move record code out of this method
		"""
		visual = None
		self._avail_rotations = []
			
		if instance is None:
			instance = self._instances[0]
			
		object = instance.getObject()
		self._namespace = object.getNamespace()
		self._object_id = object.getId()

		if angle != -1:
			del self.objectdata[self._namespace][self._object_id]
		
		if not self.objectdata.has_key(self._namespace):
			self.objectdata[self._namespace] = {}
		
		if not self.objectdata[self._namespace].has_key(self._object_id):
			self.objectdata[self._namespace][self._object_id] = {}
			
			# we hold 3 versions of the data: current, previous, default
			# default is only set one time, current and previous are changing data
			# due to the users actions
			self.objectdata[self._namespace][self._object_id]['current'] = {}
			self.objectdata[self._namespace][self._object_id]['previous'] = {}
			
			self._instance_id = instance.getId()
		
			if self._instance_id == '':
				self._instance_id = 'None'

			if angle == -1:
				angle = int(instance.getRotation())
			else:
				angle = int(angle)	
				
			self._rotation = angle
			
			if object.isBlocking():
				self._blocking = 1
				
			if object.isStatic():
				self._static = 1
			
			try:
				visual = object.get2dGfxVisual()
			except:
				print 'Fetching visual of object - failed. :/'
				raise			

			self._fixed_rotation = int(instance.getRotation() + abs( self._camera.getTilt() ) )		
			self._fixed_rotation = visual.getClosestMatchingAngle(self._fixed_rotation)	

			index = visual.getStaticImageIndexByAngle(self._fixed_rotation)

			if index == -1:
				# object is an animation
				self._animation = True
				# no static image available, try default action
				action = object.getDefaultAction()
				if action:
					animation_id = action.get2dGfxVisual().getAnimationIndexByAngle(self._fixed_rotation)
					animation = self.animationpool.getAnimation(animation_id)
					if timestamp is None and frame is not None:
						self._image = animation.getFrame(frame)	
					elif timestamp is not None and frame is None:
						self._image = animation.getFrameByTimestamp(timestamp)
					else:
						self._image = animation.getFrameByTimestamp(0)
					index = self._image.getPoolId()
			elif index != -1:
				# object is a static image
				self._animation = False
				self._image = self.imagepool.getImage(index)

			if self._animation:
				self._avail_rotations = Settings.RotAngles['animations']
			else:
				rotation_tuple = visual.getStaticImageAngles()
				for angle in rotation_tuple:
					self._avail_rotations.append( str(angle) )

# FIXME: see l. 40
			self._mapedit._objectedit_rotations = self._avail_rotations
# end FIXME
			self.write_current_data()
			
			self.objectdata[self._namespace][self._object_id]['default'] = {}
			self.objectdata[self._namespace][self._object_id]['default'] = self.objectdata[self._namespace][self._object_id]['current'].copy()
			self.objectdata[self._namespace][self._object_id]['previous'] = self.objectdata[self._namespace][self._object_id]['current'].copy()
			
			self.write_current_guidata()
		else:
			self.load_current_data()

	def dump_objectdata(self):
		"""
			just a useful dumper ^^
		"""
		print "#"*4, "Dump of objectdata", "#"*4, "\n" 
		for namespace in self.objectdata:
			print "namespace: ", namespace
			for key in self.objectdata[namespace]:
				print "\tkey: ", key
				for item in self.objectdata[namespace][key]:
					if len(item) >= 9:
						tab = "\t"*1
					else:
						tab = "\t"*2
					print "\t\t", item, " : ", tab, self.objectdata[namespace][key][item]
		
	def input(self):
		"""
			if called _and_ the user wishes to edit offsets,
			gets instance data and show gui
			
			(see run.py, pump() )
		"""
		if self._mapedit._instances != self._instances:
			if self.active is True:
				self._instances = self._mapedit._instances
				
				if self._camera is None:
					self._camera = self._mapedit._camera
					self.renderer = fife.InstanceRenderer.getInstance(self._camera)				
					
				self._layer = self._mapedit._layer
			
				if self._instances != ():
					self.highlight_selected_instance()
					self.get_instance_data()
					
					if self._animation is False:
						self.update_gui()
						self.container.adaptLayout()
						self.container.show()
						self._get_gui_size()
						self.container._setPosition(self.position)
					else:
						self.container.hide()
						print "Animation objects are not yet editable"
#					self.dump_objectdata()
				else:
					self._reset()
					self.container.hide()