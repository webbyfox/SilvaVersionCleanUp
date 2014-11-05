$Revision:  $

Copyright (c) 2007, Benno Luthiger, ETH Zurich. All rights reserved.
See also LICENSE.txt

Meta::

  Valid for:  SilvaVersionCleanUp 1.0
  Author:     Rizwan Mansuri
  Email:      mr.mansuri@gmail.com

Manage old versions

Silva retains old versions of documents for an unspecified time. 
There are various ways to remove these, thereby reducing the size of the ZODB. 
This Zope product will facilitate this.

You can add an instance of the CleanUp object somewhere in the ZMI and define 
the acceptable age of Silva Versions and the minimal number of version per document. 
After starting the CleanUp process, all Silva Documents are processed and versions 
are deleted if the document has more versions then the minimal amount and if 
the versions are older than the acceptable age.


Updates:

Added new field on form which takes Silva Publication path. Clean up can now run on individual publication and also added external method so can be called via HTTP request.
