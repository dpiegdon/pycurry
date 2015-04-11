#!/usr/bin/env python3

import inspect
import functools

def curry(lazy = True, allow_override = False, use_defaults = False):
	"""
	Decorator to create curried versions of functions. Works with python 2 and 3.

		Some examples: (for excessive examples see the testsuite at the bottom)

		>>> from curry import curry
		>>> @curry()
		... def f(x,y):
		...     print(x,y)
		... 
		>>> g = f(1)
		>>> h = g(2)
		>>> h()
		1 2

		Optionally does not wait for extra evaluation-call once all parameters have been curried:

		>>> @curry(lazy=False)
		... def k(x,y):
		...     print(x,y)
		... 
		>>> l = k(1)
		>>> l(2)
		1 2

		Optionally allows overriding of parameters already given by giving keyword parameters.

		Optionally uses the default parameters of the function.

		Decorate an existing function:

		>>> def f(x,y):
		...     print(x,y)
		... 
		>>> g = curry()(f)
		>>> h=g(1)
		>>> i=h(2)
		>>> i()
		1 2

	Authors:
		* David R. Piegdon

	License:
		You can do whatever you want with this stuff.
		If we meet some day, and you think this stuff is worth it, you can buy me a beer in return.
		The Author(s).

	Prior art and inspiration:
		* functional programming, haskell
		* python: lambda functions and functools.partial
		* https://mtomassoli.wordpress.com/2012/03/18/currying-in-python/
		* http://code.activestate.com/recipes/577928-indefinite-currying-decorator-with-greedy-call-and/
		* https://gist.github.com/JulienPalard/021f1c7332507d6a494b

	ChangeLog:
		2015-04-11 - initial implementation and testsuite
	"""

	if not ((type(lazy) is bool) and (type(allow_override) is bool) and (type(use_defaults) is bool)):
		raise TypeError("@curry used with bad parameters or none at all.")

	def _specialized_curry(fun):
		if not inspect.ismethod(fun) and not inspect.isfunction(fun):
			raise TypeError("First argument must be a function or a bound method.")
		try:
			argspec = inspect.getfullargspec(fun)
			if argspec.varargs is not None or argspec.varkw is not None:
				raise TypeError("Currying variadic function {}() is ambiguous.".format(fun.__name__))
		except AttributeError:
			# compatibility for older versions of python
			argspec = inspect.getargspec(fun)
			if argspec.varargs is not None or argspec.keywords is not None:
				raise TypeError("Currying variadic function {}() is ambiguous.".format(fun.__name__))
		if use_defaults:
			initial_args = dict( (arg, val) for (arg, val) in zip(reversed(argspec.args), reversed(argspec.defaults)) )
		else:
			initial_args = dict()
		return _curry_wrapper(fun, argspec, initial_args, lazy, allow_override)

	return _specialized_curry



# internals

def _set_argument(fun, argspec, current_args, allow_override, new_arg, new_val):
	if not new_arg in argspec.args:
		raise TypeError("{}() got an unexpected keyword argument '{}'".format(fun.__name__, new_arg))
	if new_arg in current_args and not allow_override:
		raise TypeError("Curried function {}() does not allow overriding given parameter '{}'.".format(fun.__name__, new_arg))
	current_args[new_arg] = new_val

def _first_free_arg(fun, argspec, current_args):
	for arg in argspec.args:
		if not arg in current_args:
			return arg;
	raise TypeError("{}() takes {} positional arguments but more were given".format(fun.__name__, len(argspec.args)))

def _curry_wrapper(fun, argspec, use_args, lazy, allow_override):
	@functools.wraps(fun)
	def _curried_fun(*args, **kwargs):
		current_args = dict.copy(use_args)
		def _inspect_args():
			""" stub for debugging """
			return current_args
		if 0 == len(args) and 0 == len(kwargs):
			return fun(**current_args)
		for val in args:
			_set_argument(fun, argspec, current_args, allow_override, _first_free_arg(fun, argspec, current_args), val)
		for arg in kwargs:
			_set_argument(fun, argspec, current_args, allow_override, arg, kwargs[arg])
		if not lazy and (len(current_args) == len(argspec.args)):
			return fun(**current_args)
		return _curry_wrapper(fun, argspec, current_args, lazy, allow_override)
	return _curried_fun



def _testsuite():
	### test decorator itself
	try:
		curry()(1)
		raise Exception("accepts non-function/method")
	except TypeError as e:
		if str(e) != "First argument must be a function or a bound method.":
			raise

	###
	try:
		@curry
		def d():
			pass
		raise Exception("accepts bad decorator syntax")
	except TypeError as e:
		if str(e) != "@curry used with bad parameters or none at all.":
			raise

	###
	try:
		@curry()
		def d(*args):
			pass
		raise Exception("Allows currying variadic function.")
	except TypeError as e:
		if str(e) != "Currying variadic function d() is ambiguous.":
			raise

	###
	try:
		@curry()
		def e(**kwargs):
			pass
		raise Exception("Allows currying variadic function.")
	except TypeError as e:
		if str(e) != "Currying variadic function e() is ambiguous.":
			raise

	### check general curry-properties and lazyness
	@curry(lazy = True, allow_override = False, use_defaults = False)
	def f(a,b,c,d,x=5,y=6,z=7):
		return (a,b,c,d,x,y,z)

	###
	if f(1,2,3,4,5,6,7)() != (1,2,3,4,5,6,7):
		raise Exception("Lazy currying does not work.")

	###
	if f(1,2,3,4)(5,6,7)() != (1,2,3,4,5,6,7):
		raise Exception("Multi-currying does not work.")

	###
	f1 = f(z=7)(a=1)(2)(3)(4)(5)(6)
	if not inspect.isfunction(f1):
		raise Exception("Excessive currying does not work")
	if f1() != (1,2,3,4,5,6,7):
		raise Exception("Currying with keywords does not work")

	###
	try:
		f(z=7)(2)(3)(4)(5)(6)(a=1)
		raise Exception("Overriding parameters with keyword-args is not denied.")
	except TypeError as e:
		if str(e) != "Curried function f() does not allow overriding given parameter 'a'.":
			raise

	###
	try:
		f(z=7,y=6)(1)(2)(3)(4)(5)(6)
		raise Exception("Overriding parameters is not denied.")
	except TypeError as e:
		if str(e) != "f() takes 7 positional arguments but more were given":
			raise

	###
	f2 = f(9,2,3,4)
	f3 = f2(1,1,1)
	f4 = f2(2,2,2)
	if f3() != (9,2,3,4,1,1,1) or f4() != (9,2,3,4,2,2,2):
		raise Exception("Intermediate curry-functions interfere with each other.")

	###
	try:
		f(1,2,3,4,5,6,7,8)
		raise Exception("Excessive arguments are accepted.")
	except TypeError as e:
		if str(e) != "f() takes 7 positional arguments but more were given":
			raise


	### check non-lazyness
	@curry(lazy = False, allow_override = False, use_defaults = False)
	def g(a,b,c,d,x=5,y=6,z=7):
		return (a,b,c,d,x,y,z)

	###
	g1 = g(11,12,13,14,15,16,17)
	if inspect.isfunction(g1):
		raise Exception("Non-lazy currying may be lazy.")

	###
	if g1 != (11,12,13,14,15,16,17):
		raise Exception("Non-lazy currying gives bad result.")

	###
	g2 = g(21,22,23)
	if not inspect.isfunction(g2):
		raise Exception("Intermediate non-lazy currying does not work.")

	###
	g3 = g2(24,25,26,27)
	if inspect.isfunction(g3):
		raise Exception("Excessive non-lazy currying may be lazy.")

	###
	if g3 != (21,22,23,24,25,26,27):
		raise Exception("Excessive non-lazy currying gives bad result.")

	@curry(lazy = True, allow_override = True, use_defaults = False)
	def h(a,b,c,d,x=5,y=6,z=7):
		return (a,b,c,d,x,y,z)

	if h(1,2,3,4,5,6,7,x=11,y=12,z=13)() != (1,2,3,4,11,12,13):
		raise Exception("Overridable currying gives bad result.")

	###
	h1 = h(1,2,z=7)
	try:
		h1(3,4,5,6,7)
		raise Exception("Allows overriding via positional parameters.")
	except TypeError as e:
		if str(e) != "h() takes 7 positional arguments but more were given":
			raise

	###
	if h1(3,4,5,6,z=9)() != (1,2,3,4,5,6,9):
		raise Exception("Overriding parameters from intermediate currying does not work.")

	@curry(lazy = True, allow_override = False, use_defaults = True)
	def i(a,b,c,d,x=5,y=6,z=7):
		return (a,b,c,d,x,y,z)

	if i(111,2,3,4)() != (111,2,3,4,5,6,7):
		raise Exception("Default parameters are not used")



try:
	_testsuite()
except Exception:
	print("ERROR: curry testsuite failed:")
	raise

