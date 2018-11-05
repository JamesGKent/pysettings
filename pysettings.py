import ast
import os
try:
	try:
		import winreg
	except ImportError:
		import _winreg as winreg
	HKLM = winreg.HKEY_LOCAL_MACHINE
	HKCU = winreg.HKEY_CURRENT_USER
	_windows_platform = True
except ImportError:
	HKLM = None
	HKCU = None
	_windows_platform = False
	
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

__all__ = [
	'SoftwarePrefix', 'VendorPrefix',
	'SettingsError',
	'Settings', 'DummySettings',
	'RegSettings', 'FileSettings',
	'HKLM', 'HKCU'
	]

__version__ = '0.1.1.0'

SoftwarePrefix = True
VendorPrefix = ''

class SettingsError(ValueError):
	pass

class SettingsBase(object):
	_reserved_names = ['_name', '_parent', '_children', '_changed', '_keywords', '_deletedkeywords', '_filepath']
	def __init__(self, name, parent=None, defaults=None, recursive=False):
		self._name = name
		self._keywords = []
		self._deletedkeywords = []
		self._children = []
		self._changed = False
		if parent:
			for child in parent._children:
				if child._name == name:
					raise SettingsError('sibling settings objects must have distinct names')
			parent._children.append(self)
		self._parent = parent
		if defaults:
			self.load_defaults(defaults)
		self.load(recursive)
		
	def load_defaults(self, defaults, force=False, recursedicts=False):
		if type(defaults) == dict:
			for key in defaults:
				if type(defaults[key]) == dict and recursedicts:
					s = Settings(parent=self, name=key)
					s.load_defaults(defaults[key], recursedicts=True)
				elif not hasattr(self, key) or force:
					setattr(self, key, defaults[key])
		else:
			raise ValueError("defaults must be a dict of keywords:value")
		
	def __del__(self):
		print('pysettings del %s' % self)
		try:
			self.save()
		except:
			pass
		if self._parent:
			self._parent._children.remove(self)
		
	def __getattr__(self, name):
		if name == 'children':
			return [child._name for child in self._children]
		else:
			return object.__getattr__(self, name)
		
	def __setattr__(self, name, val):
		if name not in self._reserved_names:
			if name not in self._keywords:
				self._keywords.append(name)
			if hasattr(self, name):
				if getattr(self, name) != val:
					self._changed = True
			else:
				self._changed = True
			if name in self._deletedkeywords:
				self._deletedkeywords.remove(name)
		# if callable and we have a value already
		if callable(val) and hasattr(self, name):
			if not callable(getattr(self, name)):
				val(getattr(self, name)) # call func with value
		self.__dict__[name] = val
		
	def __delattr__(self, name):
		self._keywords.remove(name)
		self._deletedkeywords.append(name)
		self._changed = True
		object.__delattr__(self, name)
		
	def __getitem__(self, name):
		if name == 'children':
			return [child._name for child in self._children]
		for child in self._children:
			if child._name == name:
				return child
		raise KeyError
		
	def load(self):
		pass
		
	def save(self):
		for child in self._children:
			child.save()
			
	def delete(self):
		for child in self._children:
			child.delete()
		if self._parent:
			self._parent._children.remove(self)
			
class DummySettings():
	_reserved_names = ['_name', '_parent', '_keywords']
	def __init__(self, parent, name, value, dupe_check=True):
		if dupe_check:
			for child in parent._children:
				if child._name == name:
					raise SettingsError('sibling settings objects must have distinct names')
		self._keywords = [name]
		self._name = name
		if not dupe_check and name not in parent._children:
			parent._children.append(self)
		parent.__setattr__(name, value)
		self._parent = parent
		
	def __setattr__(self, name, value):
		if name not in self._reserved_names:
			if name in self._keywords:
				self._parent.__setattr__(name, value)
			else:
				self.keywords.append(name)
				DummySettings(self._parent, name, value)
		self.__dict__[name] = value
		
	def __delattr__(self, name):
		self._parent.__delattr__(name)
		
	def load(self):
		pass
		
	def save(self):
		pass
		
	def delete(self):
		self.__delattr__(self._name)
		
def CreateKeyPath(name, parent=None):
	if parent:
		return os.path.join(parent, name)
	parts = []
	if SoftwarePrefix:
		parts.append('Software')
	if VendorPrefix != '':
		parts.append(VendorPrefix)
	parts.append(name)
	return os.path.join(*parts)

class RegSettings(SettingsBase):
	_reserved_names = SettingsBase._reserved_names + ['_keytype', '_keypath']
	def __init__(self, keytype=None, name=None, parent=None, defaults=None, recursive=False):
		if (name==None):
			raise ValueError('name must be given')
		if (keytype==None and parent==None) or (keytype!=None and parent!=None):
			raise ValueError('either keytype or parent is required')
		if parent:
			try:
				self._keytype = parent._keytype
				self._keypath = CreateKeyPath(name, parent._keypath)
			except AttributeError:
				raise ValueError('parent must be a settings class instance')
		else:
			self._keytype = keytype
			self._keypath = CreateKeyPath(name)
		SettingsBase.__init__(self, name, parent, defaults, recursive)
		
	def load(self, recursive=False):
		try:
			rootkey = winreg.OpenKey(self._keytype, self._keypath, 0, winreg.KEY_READ)
		except OSError: # key doesn't exist
			return
		values = winreg.QueryInfoKey(rootkey)[1]
		for num in range(0, values):
			name, data, datatype = winreg.EnumValue(rootkey, num)
			try:
				SettingsBase.__setattr__(self, name, ast.literal_eval(data))
			except (ValueError, SyntaxError):
				raise SettingsError("Error")
		if recursive:
			keys, vals, mod = winreg.QueryInfoKey(rootkey)
			for i in range(0, keys):
				name = winreg.EnumKey(rootkey, i)
				s = Settings(parent=self, name=name, recursive=True)
		
	def save(self):
		if self._changed:
			try:
				rootkey = winreg.OpenKey(self._keytype, self._keypath, 0, winreg.KEY_WRITE)
			except FileNotFoundError:
				rootkey = winreg.CreateKey(self._keytype, self._keypath)
			for keyword in self._keywords:
				attr = getattr(self, keyword)
				if callable(attr):
					val = repr(attr())
				else:
					val = repr(attr)
				winreg.SetValueEx(rootkey, keyword, 0, winreg.REG_SZ, val)
			for keyword in self._deletedkeywords:
				try:
					winreg.DeleteValue(rootkey, keyword)
				except FileNotFoundError:
					pass
			self._changed = False
		SettingsBase.save(self)
		
	def delete(self):
		for child in list(self._children):
			child.delete()
		winreg.DeleteKey(self._keytype, self._keypath)
		SettingsBase.delete(self)
		
class FileSettings(SettingsBase):
	_reserved_names = SettingsBase._reserved_names + ['_filepath', '_name', '_node']
	def __init__(self, filepath=None, name=None, parent=None, defaults=None, recursive=False):
		if (name==None):
			raise ValueError("name must be provided")
		if (filepath==None and parent==None):
			raise ValueError("either filepath or a parent must be provided")
		if parent:
			if hasattr(parent, '_filepath'):
				self._filepath = None
			else:
				raise ValueError('parent must be a settings class instance')
		else:
			self._filepath = filepath
		self._name = name
		
		SettingsBase.__init__(self, name, parent, defaults, recursive)
		
	def load(self, recursive=False):
		if self._filepath:
			try:
				tree = ET.parse(self._filepath)
				self._node = tree.getroot()
			except FileNotFoundError:
				self._node = None
				return
			if self._node.tag != self._name:
				raise SettingsError("settings file root node doesn't match this settings object")
			for child in self._node:
				if child.get('value', '0') == '1':
					setattr(self, child.tag, ast.literal_eval(child.text))
		else:
			if self._parent._node is None:
				self._node = None
			else:
				self._node = self._parent._node.find(self._name)
				if self._node != None:
					for child in self._node:
						if child.get('value', '0') == '1':
							SettingsBase.__setattr__(self, child.tag, ast.literal_eval(child.text))
		if recursive:
			if self._node != None:
				for child in self._node:
					if child.get('value', '0') == '0':
						s = Settings(parent=self, name=child.tag, recursive=True)
		
	def save(self):
		if self._filepath:
			self._node = ET.Element(self._name)
		else:
			self._node = ET.SubElement(self._parent._node, self._name)
		for keyword in self._keywords:
			attr = getattr(self, keyword)
			if callable(attr):
				val = repr(attr())
			else:
				val = repr(attr)
			e = ET.SubElement(self._node, keyword)
			e.text = val
			e.set('value', '1')
		SettingsBase.save(self)
		if self._filepath:
			tree = ET.ElementTree(self._node)
			tree.write(self._filepath)

def Settings(keytype=None, filepath=None, name=None, parent=None, defaults=None, recursive=False):
	if (parent):
		if isinstance(parent, RegSettings):
			return RegSettings(None, name, parent, defaults, recursive)
		elif isinstance(parent, FileSettings):
			return FileSettings(filepath, name, parent, defaults, recursive)
		else:
			raise SettingsError('parent must be an instance of a settings class')
	else:
		if (keytype and _windows_platform):
			return RegSettings(keytype, name, None, defaults, recursive)
		else:
			return FileSettings(filepath, name, None, defaults, recursive)
