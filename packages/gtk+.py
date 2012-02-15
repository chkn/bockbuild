class GtkPackage (GnomePackage):
	def __init__ (self):
		GnomePackage.__init__ (self, 'gtk+',
			version_major = '2.24',
			version_minor = '8',
			configure_flags = [
				'--with-gdktarget=%{gdk_target}',
				'--prefix="%{prefix}"'
#				'--disable-cups',
			]
		)
		self.configure = './configure'
		self.gdk_target = 'x11'

		if Package.profile.name == 'darwin':
			self.gdk_target = 'quartz'
			self.sources.extend ([
					# Custom gtkrc
					'patches/gtkrc',

					# post-2.24.8 commits from 2.24 branch
					# quartz: fix a race condition when waking up the CGRunLoopgtk
					'http://git.gnome.org/browse/gtk+/patch/?id=0729cdc9a1e8003c41d3ebf20eecfe2d1b29ffbe',
					# Revert "iconview: layout items immediately when setting a GtkTreeModel"
					'http://git.gnome.org/browse/gtk+/patch/?id=5c3bb1839cac52828756f9ddb98f49d586853991',
					# notebook: don't leak the action widgets
					'http://git.gnome.org/browse/gtk+/patch/?id=4c35d987dfe3b169f0448d5c27e5ebad06f91cab',
					# Bug 663856 - Make option-foo accelerators use the right symbol
					'http://git.gnome.org/browse/gtk+/patch/?id=2e06f63743010da065f59234e7f5062205e31b43',
					# [Bug 664238] GTK apps crash when dragging somethinggtk
					'http://git.gnome.org/browse/gtk+/patch/?id=7c77f9a69ab4dfea9f015cf09db6d501576523aa',

					# smooth scrolling, https://bugzilla.gnome.org/show_bug.cgi?id=516725
					'http://bugzilla-attachments.gnome.org/attachment.cgi?id=201916',

					# make new modifier behviour opt-in, so as not to break old versions of MonoDevelop
					'patches/gdk-quartz-set-fix-modifiers-hack.patch',
			])

	def prep (self):
		Package.prep (self)
		if Package.profile.name == 'darwin':
			for p in range (2, len (self.sources)):
				self.sh ('patch -p1 < "%{sources[' + str (p) + ']}"')

	def install(self):
		Package.install(self)
		self.install_gtkrc ()

	def install_gtkrc(self):
		origin = os.path.join (self.package_dest_dir (), os.path.basename (self.sources[1]))
		destdir = os.path.join (self.prefix, "etc", "gtk-2.0")
		if not os.path.exists (destdir):
			os.makedirs(destdir)
		self.sh('cp %s %s' % (origin, destdir))

GtkPackage ()
