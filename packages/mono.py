class MonoPackage (Package):
	def __init__ (self):
		Package.__init__ (self, 'mono', '2.11',
			sources = [
				'http://download.mono-project.com/sources/%{name}/%{name}-%{version}.tar.bz2',
				#'patches/mono-gtk-sharp-profiler.patch'
			],
			configure_flags = [
				'--prefix=' + Package.profile.prefix,
				'--with-jit=yes',
				'--with-ikvm=yes',
				#'--with-mcs-docs=no',
				'--with-moonlight=no',
				#'--enable-quiet-build',
			]
		)
		if Package.profile.name == 'darwin':
			self.configure_flags.extend ([
				# fix build on lion, it uses 64-bit host even with -m32
				'--build=i386-apple-darwin11.2.0',
				'--enable-loadedllvm'
			])

		# Mono (in libgc) likes to fail to build randomly
		self.make = 'for i in 1 2 3 4 5 6 7 8 9 10; do make && break; done'

#	def prep (self):
#		Package.prep (self)
#		self.sh ('patch -p1 < "%{sources[1]}"')

MonoPackage ()
