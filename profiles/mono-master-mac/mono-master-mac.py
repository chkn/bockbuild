#!/usr/bin/python -B

import fileinput, glob, os, pprint, re, sys, tempfile, shutil

sys.path.append ('../..')

from bockbuild.darwinprofile import DarwinProfile
from bockbuild.util import *
from packages import MonoMasterPackages

class MonoMasterProfile (DarwinProfile, MonoMasterPackages):
	def __init__ (self):
		self.MONO_ROOT = "/Library/Frameworks/Mono.framework"
		self.RELEASE_VERSION = "2.11" # REMEMBER TO UPDATE
		self.BUILD_NUMBER = "0"
		self.MRE_GUID = "432959f9-ce1b-47a7-94d3-eb99cb2e1aa8"
		self.MDK_GUID = "964ebddd-1ffe-47e7-8128-5ce17ffffb05"

		# Create the updateid
		parts = self.RELEASE_VERSION.split(".")
		version_list = ( parts + ["0"] * (3 - len(parts)) )[:4]
		version_list = [version_list[i].zfill(2) for i in range (1,3)]
		self.updateid = "".join(version_list)
		self.updateid += self.BUILD_NUMBER.replace(".", "").zfill(9 - len(self.updateid))

		versions_root = os.path.join (self.MONO_ROOT, "Versions")
		self.release_root = os.path.join (versions_root, self.RELEASE_VERSION)

		DarwinProfile.__init__ (self, self.release_root)
		MonoMasterPackages.__init__ (self)

		self_dir = os.path.realpath (os.path.dirname (sys.argv[0]))
		self.packaging_dir = os.path.join (self_dir, "packaging")

		aclocal_dir = os.path.join (self.prefix, "share", "aclocal")
		if not os.path.exists(aclocal_dir):
			os.makedirs (aclocal_dir)

	def framework_path (self, subdir):
		return os.path.join (self.prefix, subdir)

	def remove_files (self, subdir = "lib", prefix = "*"):
		dir = os.path.join (self.prefix, subdir)
		print "Removing %s files in %s" % (prefix, dir)
		backtick ('find %s -name "%s" -delete' % (dir, prefix))

	def include_libgdiplus (self):
		config = os.path.join (self.prefix, "etc", "mono", "config")
		temp = config + ".tmp"
		lib = self.framework_path("lib")
		with open(config) as c:
			with open(temp, "w") as output:
				for line in c:
					if re.search(r'</configuration>', line):
						# Insert libgdiplus entries before the end of the file
						output.write('\t<dllmap dll="gdiplus" target="%slibgdiplus.dylib" />\n' % lib)
						output.write('\t<dllmap dll="gdiplus.dll" target="%slibgdiplus.dylib" />\n' % lib)
					output.write(line)

		os.rename(temp, config)

	def make_package_symlinks(self, root):
		os.symlink (self.prefix, os.path.join (root, "Versions", "Current"))
		links = [
			("bin", "Commands"),
			("include", "Headers"),
			("lib", "Libraries"),
			("", "Home"),
			(os.path.join ("lib", "libmono-2.0.dylib"), "Mono")
		]
		for srcname, destname in links:
			src  = os.path.join (self.prefix, srcname)
			dest = os.path.join (root, destname)
			if os.path.exists (dest):
				os.unlink (dest)
			os.symlink (src, dest)

	def prepare_package (self):
		tmpdir = tempfile.mkdtemp()
		monoroot = os.path.join (tmpdir, "PKGROOT", self.MONO_ROOT[1:])
		versions = os.path.join (monoroot, "Versions")
		os.makedirs (versions)

		# setup metadata
		backtick ('rsync -aP %s/* %s' % (self.packaging_dir, tmpdir))
		parameter_map = {
			'@@MONO_VERSION@@': self.RELEASE_VERSION,
			'@@MONO_RELEASE@@': self.BUILD_NUMBER,
			'@@MONO_VERSION_RELEASE@@': self.RELEASE_VERSION + '_' + self.BUILD_NUMBER,
			'@@MONO_PACKAGE_GUID@@': self.MRE_GUID,
			'@@MONO_CSDK_GUID@@': self.MDK_GUID,
			'@@MONO_VERSION_RELEASE_INT@@': self.updateid,
			'@@PACKAGES@@': "FIXME",
			'@@DEP_PACKAGES@@': "FIXME"
		}
		for dirpath, d, files in os.walk (tmpdir):
			for name in files:
				if not name.startswith('.'):
					replace_in_file (os.path.join (dirpath, name), parameter_map)

		self.make_package_symlinks(monoroot)

		# copy to package root	
		backtick ('rsync -aP %s %s' % (self.release_root, versions))

		return tmpdir

	def run_package_maker (self, output, prepared_package, title):
		packagemaker = '/Developer/Applications/Utilities/PackageMaker.app/Contents/MacOS/PackageMaker'
		cmd = ' '.join([packagemaker,

			"--resources '%s/resources'" % prepared_package,
			"--info '%s/Info.plist'" % prepared_package,
			"--root '%s/PKGROOT'" % prepared_package,

			"--out '%s'" % output,
			"--title '%s'" % title,
			"-x '.DS_Store'"
		])
		#print cmd
		backtick (cmd)

	def make_dmg (self, output, package, volname):
		dmgroot = os.path.join (os.path.dirname (package), "DMGROOT")
		os.mkdir (dmgroot)
		backtick ('mv %s %s' % (package, dmgroot))
		backtick ('hdiutil create -ov -srcfolder %s -volname %s %s' % (dmgroot, volname, output))

	def build_package (self):
		out_path = os.getcwd ()
		tmp_path = self.prepare_package ()

		mdk_path = os.path.join (tmp_path, "MonoFramework-MDK-%s.macos10.xamarin.x86.pkg" % self.RELEASE_VERSION)
		mdk_dmg_path = os.path.join (out_path, "MonoFramework-MDK-%s.macos10.xamarin.x86.dmg" % self.RELEASE_VERSION)
		self.run_package_maker (mdk_path, tmp_path, 'Mono Framework MDK ' + self.RELEASE_VERSION)
		self.make_dmg (mdk_dmg_path, mdk_path, 'MonoFramework-MDK-' + self.RELEASE_VERSION)
		
		shutil.rmtree (tmp_path)

	# THIS IS THE MAIN METHOD FOR MAKING A PACKAGE
	def package (self):
		self.remove_files (prefix = '*.la')
		self.remove_files (prefix = '*.a')
		self.include_libgdiplus ()
		self.build_package ()

MonoMasterProfile ().build ()

profname = "mono-master-mac-env"
dir = os.path.realpath (os.path.dirname (sys.argv[0]))
envscript = '''#!/bin/sh
PROFNAME="%s"
INSTALLDIR=%s/build-root/_install
export DYLD_FALLBACK_LIBRARY_PATH="$INSTALLDIR/lib:/lib:/usr/lib:$DYLD_FALLBACK_LIBRARY_PATH"
export C_INCLUDE_PATH="$INSTALLDIR/include:$C_INCLUDE_PATH"
export ACLOCAL_PATH="$INSTALLDIR/share/aclocal:$ACLOCAL_PATH"
export ACLOCAL_FLAGS="-I $INSTALLDIR/share/aclocal $ACLOCAL_FLAGS"
export PKG_CONFIG_PATH="$INSTALLDIR/lib/pkgconfig:$INSTALLDIR/lib64/pkgconfig:$INSTALLDIR/share/pkgconfig:$PKG_CONFIG_PATH"
export CONFIG_SITE="$INSTALLDIR/$PROFNAME-config.site"
export MONO_GAC_PREFIX="$INSTALLDIR:MONO_GAC_PREFIX"
export MONO_ADDINS_REGISTRY="$INSTALLDIR/addinreg"
export PATH="$INSTALLDIR/bin:$PATH"
export MONO_INSTALL_PREFIX="$INSTALLDIR"

#mkdir -p "$INSTALLDIR"
#echo "test \"\$prefix\" = NONE && prefix=\"$INSTALLDIR\"" > $CONFIG_SITE

PS1="[$PROFNAME] \w @ "
''' % ( profname, dir )

with open(os.path.join (dir, profname), 'w') as f:
	f.write (envscript)
