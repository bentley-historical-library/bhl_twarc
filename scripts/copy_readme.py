import os
import shutil

def copy_readme(feeds, readme_file):
	if os.path.exists(readme_file):
		for feed in feeds:
			print "Verifying README for {0}".format(feed)
			feed_dict = feeds[feed]
			feed_dir = feed_dict["feed_dir"]
			feed_readme = os.path.join(feed_dir, "README.txt")
			if not os.path.exists(feed_readme):
				print "Copying README"
				shutil.copy(readme_file, feed_dir)
			else:
				print "README already exists"
	else:
		print "No README file found"