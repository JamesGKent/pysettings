# PySettings

classes to use for storing app settings in python.

## To use:
```
s = Settings(*args) # create an instance
# give the settings class attributes
s.boolean = True
s.string = "i'm a string"
s.save() # save
```

## Types of settings classes:
### RegSettings - Windows
the RegSettings class has the following arguments:
 - keytype - should be a winreg constant such as winreg.HKEY_CURRENT_USER (if doesn't have parent)
 - name - a name for this key level of settings
 - parent - should be another instance of a settings object (if not the top level)
 - defaults - a dictionary of default attributes (if required)

If a parent is specified the keytype should be `None` and the parents name attribute is used to build the path to this level of settings.
note that the save method is only required on the top level settings object, as it recursively calls all child settings objects `save` method

### FileSettings - non windows platforms e.g. linux, MacOS, BSD etc
the FileSettings class has the following arguments:
 - filepath - should be a path to the settings file (if doesn't have parent)
 - name - a name for this level of settings
 - parent - should be another instance of a settings object (if not the top level)
 - defaults - a dictionary of default attributes (if required)

If a parent is specified the filepath should be `None` and the parents name attribute is used to build the path to this level of settings.
note that the save method is only required on the top level settings object, as it recursively calls all child settings objects `save` method

### Settings - wrapper
the 'Settings' function is a wrapper that accepts all possible arguments of 'RegSettings' or 'FileSettings' to return the most appropriate. if a prent is provided then the returned object will be the same type as the parent.
if keytype is provided and the platform is windows then the RegSettings object is used. if platform is not windows or the keytype is not provided then FileSettings is used. if anything required by the chosen class is missing then that class will raise an error.
this wrapper can be used to provide cross platform capability using the registry if desired, or only using files.

### Attributes
attributes of either type of settings object can be any of the following:
 - strings
 - bytes
 - int
 - float
 - tuples
 - lists
 - dicts
 - sets
 - booleans
 - None


### Functions as attributes
also attributes can be a function that optionally accepts or returns on of the above types, this way when the save is called the function is called to get the value, and upon loading the saved value is passed to the function.
E.g.

```
def test_function(arg=None):
	if arg:
		print(arg)
	else:
		return "i'm new"
s = pysettings.Settings(filepath='./test.xml', name='functiontest')
s.func = test_function
```  

## Notes
 - while sibling settings objects cannot have the same name, a settings object can have an attribute and a child settings object with the same name.