#!/usr/bin/perl
use strict;
use warnings FATAL=>'all';
use open ':utf8';
use utf8;

use Data::Dumper;

########################################################################
# Global variables
########################################################################

my $USER = 'me';
my $MIN_NB_OF_LINKS = 0;
my $REFNAME_PROPERTY = ''; # if empty, don't use
my $USE_SCHEMATA = '';
my $INPUT_FILE = '';
my $OUTPUT_FILE_CORPUS = '';
my $OUTPUT_FILE_ANNOTATIONS = '';
my $OUTPUT_FILE_MODEL = '';
my $DONT_KEEP_COMMENTS = '';
my $EMPTY_REFNAME_FIELD = '';
my $EMPTIED_REFNAME_FIELD_VALUE = '';
my $BUILD_GLOZZ_MODEL = '';
my $EXPLODE_HEAD = '';
my $LINK_NAME = '';
my %FILTER = ();

$Data::Dumper::Terse  = 1;
$Data::Dumper::Indent = 1;

########################################################################
# Get the CLI parameters
########################################################################

my $HELP =<<"END";
USAGE
  $0 [OPTIONS] INPUT OUTPUT

DESCRIPTION
  Convert a SACR file to a couple of Glozz files (.ac and .aa).
  Do not specify the extensions (.ac/.aa) for the output file.

OPTIONS (-o value --opt value)
   -h             Print help.
   -m --min VALUE The minimum length of a chain.  If -e AND -p are set, then
                  the chains with less links have the value specified in -e.
                  Otherwise, they are excluded.
                  Default is 0 (all links are included).
   -e VALUE       Put VALUE in the the PROP_NAME property (if the -p option is
                  used) for chains with less than -m. (E.g. "" or "SI" for
                  SIngleton.)
   -p PROP_NAME   Include a property PROP_NAME with the name of the referent.
                  If empty string, don't use.
   -s --schema    Include schemata.
   -K             Don't keep comments.
   -e             Explode head property into 'headpos' and 'headstring'.
   -f REFNAME     Include only REFNAME (this option can be repeated).
   --model        Build a Glozz annotation model (.aam).
   --link-name VAL Name of the link (like 'link', 'mention', 'markable', etc.).
                  Default is 'MENTION'.
END

sub get_cl_parameters {

   # default
   $MIN_NB_OF_LINKS = 0;
   $REFNAME_PROPERTY = '';
   $USE_SCHEMATA = '';
   $INPUT_FILE = '';
   $OUTPUT_FILE_CORPUS = '';
   $OUTPUT_FILE_ANNOTATIONS = '';
   $OUTPUT_FILE_MODEL = '';
   $EXPLODE_HEAD = '';
   $DONT_KEEP_COMMENTS = '';
   $EMPTY_REFNAME_FIELD = '';
   $EMPTIED_REFNAME_FIELD_VALUE = '';
   $BUILD_GLOZZ_MODEL = '';
   $LINK_NAME = 'MENTION';

   my $pending = '';

   for (@ARGV) {
      print $HELP and exit if m/^(?:-h|--?help)$/;
      last if $pending and m/^-/;
      # pending
      if ($pending eq '-m' and m/^\d++$/) {
         $MIN_NB_OF_LINKS = $_;
         $pending = '';
      } elsif ($pending eq '-f') {
         $FILTER{$_} = 1;
         $pending = '';
      } elsif ($pending eq '-e') {
         $EMPTY_REFNAME_FIELD = 1;
         $EMPTIED_REFNAME_FIELD_VALUE = $_;
         $pending = '';
      } elsif ($pending eq '-p') {
         $REFNAME_PROPERTY = $_;
         $pending = '';
      } elsif ($pending eq '--link-name') {
         $LINK_NAME = $_;
         $pending = '';
      # end of pending
      } elsif ($pending) {
         last;
      # options with value waiting for next element in @ARGV
      } elsif (m/^(?:-m|--min)$/) {
         $pending = '-m';
      } elsif (m/^-f$/) {
         $pending = '-f';
      } elsif (m/^--link-name$/) {
         $pending = '--link-name';
      } elsif (m/^(?:-p|--property)$/) {
         $pending = '-p';
      } elsif (m/^(?:-e)$/) {
         $pending = '-e';
      # switch (= options with no value)
      } elsif (m/^(?:-s|--schema)$/) {
         $USE_SCHEMATA = 1;
      } elsif (m/^--model$/) {
         $BUILD_GLOZZ_MODEL = 1;
      } elsif (m/^-K$/) {
         $DONT_KEEP_COMMENTS = 1;
      } elsif (m/^-e$/) {
         $EXPLODE_HEAD = 1;
      # end of options
      } elsif (m/^-.+/) {
         die "$0: *** option '$_' doesn't exists ***\n";
      # arguments, not options
      } elsif (!$INPUT_FILE) {
         $INPUT_FILE = $_;
      } elsif (!$OUTPUT_FILE_CORPUS) {
         $OUTPUT_FILE_CORPUS = "$_.ac";
         $OUTPUT_FILE_ANNOTATIONS = "$_.aa";
         $OUTPUT_FILE_MODEL = "$_.aam";
      } else {
         die "$0: *** bad argument '$_' ***\n";
      }
   } # for

   die "$0: *** missing value for option '$pending' ***\n" if $pending;

   die "$0: *** no input/output file ***\n"
      unless $INPUT_FILE and $OUTPUT_FILE_ANNOTATIONS and $OUTPUT_FILE_CORPUS
      and $OUTPUT_FILE_MODEL;

   die "$0: *** file '$INPUT_FILE' doesn't exist ***\n"
      unless -f-r $INPUT_FILE;

}


########################################################################
# parser
########################################################################

sub parse {

   my $content = shift;
   my $r_filter = shift;

   my $corpus = '';
   my @paragraphs = (); # format: { start=>0, end=>0 }
   my @annotations = (); # format: [ start=>0, end=>0, offset=>LEN_CORPUS, name=>NAME props => {props} ]
   my @filoAnnotations = ();

   # each line is a paragraph
   for my $line (split /\n/, $content) {
      chomp $line;
      if ($line =~ m/^\s*+$/) {
         # nothing
      } elsif ($line =~ m/^\s*+#.*+$/ or $line =~ m/^\*++$/) {
         unless ($DONT_KEEP_COMMENTS) {
            push @paragraphs, { start=>length($corpus), end=>length($corpus)+length($line) };
            $corpus .= $line;
         } else {
            # nothing
         }
      } else {
         my $plain_text = '';
         pos($line) = 0;
         while (pos($line) < length $line) {
            if ($line =~ m/\G\{([-_0-9a-zA-Z]++)/gc) {
               my $refname = $1;
               my %props = ();
               if ($line =~ m/\G:/gc) {
                  while ($line =~ m/\G([-_0-9a-zA-Z]++)=(?:"([^"]*+)"|([-_0-9a-zA-Z]++)),?/gc) {
                     #print "DEBUG: $1\n";
                     if ($1 eq 'head' and $EXPLODE_HEAD and
                           $2 =~ m/^\s*+(\d++)\s*+:\s*+(.++)$/) {
                        $props{headpos} = $1;
                        $props{headstring} = $2;
                     } else {
                        if (length $2) {
                           $props{$1} = $2;
                        } elsif (length $3) {
                           $props{$1} = $3;
                        } else {
                           $props{$1} = "";
                        }
                     }
                  }
               }
               $props{$REFNAME_PROPERTY} = $refname if $REFNAME_PROPERTY;
               unless ($line =~ m/\G\s/gc) {
                  die "$0: *** ill formed line: $line (no space after properties) ***\n";
               }
               push @filoAnnotations, {
                     start => length $plain_text,
                     end => undef,
                     name => $refname,
                     props => { %props },
                     offset => length $corpus
                  };
            } elsif ($line =~ m/\G\}/gc) {
               die "$0: *** too many {'s ***\n" unless @filoAnnotations;
               $filoAnnotations[-1]->{end} = length $plain_text;
               push @annotations, pop @filoAnnotations;
            } elsif ($line =~ m/\G(.)/gc) {
               $plain_text .= $1;
            }
         } # while
         die "$0: *** filo not empty for line: $line ***\n" if @filoAnnotations;
         die "$0: *** string not completed ***\n" unless pos($line) == length($line);
         # set the paragraph
         push @paragraphs, { start=>length($corpus), end=>length($corpus)+length($plain_text) };
         $corpus .= $plain_text;
      } # if
   } # for

   my $counter = time();
   my $xml = '';
   for (@paragraphs) {
      $xml .= "<unit id=\"${USER}_$counter\">\n";
      $xml .= "<metadata><author>$USER</author><creation-date>$counter</creation-date></metadata>\n";
      $xml .= "<characterisation><type>paragraph</type><featureSet /></characterisation>\n";
      $xml .= sprintf '<positioning><start><singlePosition index="%d" /></start><end><singlePosition index="%d" /></end></positioning>'."\n",
         $_->{start}, $_->{end};
      $xml .= "</unit>\n";
      $counter++;
   }

   my %property_list = ();
   for my $annot (@annotations) {
      for my $prop (keys %{$annot->{props}}) {
         $property_list{$prop} = 1;
      }
   }

   my %chains = ();
   for (@annotations) {
      if (exists $chains{$_->{name}}) {
         $chains{$_->{name}}++;
      } else {
         $chains{$_->{name}} = 0;
      }
   }

   my %schemata = (); # format: REFNAME => [ IDCOUNTER, IDCOUNTER, ... ]
   for (@annotations) {
      next if %$r_filter and not $r_filter->{$_->{name}};
      if ($chains{$_->{name}} < $MIN_NB_OF_LINKS) {
         if ($EMPTY_REFNAME_FIELD and $REFNAME_PROPERTY) {
            $_->{props}->{$REFNAME_PROPERTY} = $EMPTIED_REFNAME_FIELD_VALUE;
         } else {
            next;
         }
      }
      $xml .= "<unit id=\"${USER}_$counter\">\n";
      $xml .= "<metadata><author>$USER</author><creation-date>$counter</creation-date></metadata>\n";
      $xml .= "<characterisation>\n";
      if ($_->{name} =~ m/^_/) {
         (my $name = $_->{name}) =~ s/^_//;
         $xml .= "<type>$name</type>\n", ;
      } else {
         $xml .= "<type>$LINK_NAME</type>\n";
      }
      $xml .= "<featureSet>\n";
      for my $k (keys %{$_->{props}}) {
         my $val = $_->{props}->{$k};
         $xml .= "<feature name=\"$k\">$val</feature>\n";
      }
      $xml .= "</featureSet>\n";
      $xml .= "</characterisation>\n";
      $xml .= sprintf '<positioning><start><singlePosition index="%d" /></start><end><singlePosition index="%d" /></end></positioning>'."\n",
         $_->{start}+$_->{offset}, $_->{end}+$_->{offset};
      $xml .= "</unit>\n";
      if (exists $schemata{$_->{name}}) {
         # for the format of the ID, see embedded-unit below
         push @{$schemata{$_->{name}}}, "${USER}_$counter";
      } else {
         $schemata{$_->{name}} = [ "${USER}_$counter" ];
      }
      $counter++;
   }

   if ($USE_SCHEMATA) {
      for my $k (keys %schemata) {
         next if $k =~ m/^_/;
         next if scalar @{$schemata{$k}} < $MIN_NB_OF_LINKS;
         $xml .= "<schema id=\"${USER}_$counter\">\n";
         $xml .= "<metadata><author>$USER</author><creation-date>$counter</creation-date></metadata>\n";
         $xml .= "<characterisation><type>cr</type>\n";
         $xml .= "<featureSet>\n";
         $xml .= "<feature name=\"nom\">$k</feature>\n";
         $xml .= "</featureSet>\n";
         $xml .= "</characterisation>\n";
         $xml .= "<positioning>\n";
         for my $id (@{$schemata{$k}}) {
            # NOTE: 'id' is not the id of the unit! It is in fact
            # "AUTHOR_CREATIONDATE" of the unit, and the 'id' of the
            # unit is in fact not used!
            $xml .= "<embedded-unit id=\"$id\"/>\n";
         }
         $xml .= "</positioning>\n";
         $xml .= "</schema>\n";
         $counter++;
      }
   }

   my $model = "";

   if ($BUILD_GLOZZ_MODEL) {
      $model = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n";
      $model .= "<annotationModel>\n";
      $model .= "<units>\n";
      $model .= "<type name=\"$LINK_NAME\">\n";
      for my $property (keys %property_list) {
         $model .= "<featureSet>\n";
         $model .= "<feature name=\"$property\">\n";
         $model .= "<value type=\"free\" default=\"\" />\n";
         $model .= "</feature>\n";
         $model .= "</featureSet>\n";

      }
      $model .= "</type>\n";
      $model .= "</units>\n";
      $model .= "<relations>\n";
      $model .= "</relations>\n";
      $model .= "<schemas>\n";
      $model .= "</schemas>\n";
      $model .= "</annotationModel>\n";
   }

   return ($corpus,
      "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<annotations>\n$xml</annotations>\n",
      $model);

}


########################################################################
# Helper functions
########################################################################


sub confirm_yn {

	my $message = shift || 'Confirm ? (y|n) ';
	my $default = shift;

	ITER: {
		print $message;
		my $ans = <STDIN>;
		print "\n" unless -t STDIN;
		return 1 if $ans =~ m/^\s*+y(?:es)?\s*+$/;
		return 0 if $ans =~ m/^\s*+n(?:o)?\s*+$/;
		return $default if (defined($default) and $ans =~ m/^\s*+$/);
		redo ITER;
	}

}

sub read_file {

   my $file = shift;

   open my $fh, $file or die "$0: *** can't open $file ***\n";

   local $/ = undef;

   my $content = <$fh>;

   close $fh or die "$0: *** can't close $file ***\n";

   return $content;

}

sub write_file {

   my $file = shift;
   my $content = shift;

   open my $fh, ">", $file or die "$0: *** can't open $file ***\n";
   print $fh $content;
   close $fh or die "$0: *** can't close $file ***\n";

}


########################################################################
# main()
########################################################################

sub main {

   get_cl_parameters();

   if (-e $OUTPUT_FILE_ANNOTATIONS or -e $OUTPUT_FILE_CORPUS or -e
         $OUTPUT_FILE_MODEL) {
      return unless (confirm_yn("Output files exist.  Overwrite [Y/n]?", 1));
   }

   my $content = read_file($INPUT_FILE);

   my ($corpus, $xml, $model) = parse($content, \%FILTER);
   write_file($OUTPUT_FILE_CORPUS, $corpus);
   write_file($OUTPUT_FILE_ANNOTATIONS, $xml);
   if ($OUTPUT_FILE_MODEL) {
      write_file($OUTPUT_FILE_MODEL, $model);
   }

   return 1;

}


main()
   and print "$0: done!\n";


