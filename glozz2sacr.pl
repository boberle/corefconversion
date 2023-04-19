#!/usr/bin/perl
use strict;
use warnings FATAL=>'all';
use open ':utf8';
use utf8;

use Data::Dumper;
#use XML::LibXML::Simple   qw(XMLin);
use XML::Simple   qw(XMLin);


########################################################################
# Global variables
########################################################################

my $INPUT_CORPUS = '';
my $INPUT_ANNOTATIONS = '';
my $OUTPUT_FILE = '';
my $REFNAME_FIELD = ''; # REF, refname, etc.
my $UNIT_TYPE = ''; # maillon, MENTION, etc.
my $RESET_REFNAME_FIELD = '';

$Data::Dumper::Terse  = 1;
$Data::Dumper::Indent = 1;


########################################################################
# Get the CLI parameters
########################################################################

my $HELP =<<"END";
USAGE
  $0 [OPTIONS] INPUT_AND_OUTPUT_FILES

EXAMPLE:
  $0 test.aa output

DESCRIPTION
  Convert a couple of Glozz files to a SACR file.  You can give the FILES
  in any order: the .ac and .aa files will be determined by their
  extensions.  You can give only one of the Glozz file: the other will be
  found (if in the same directory).  If no output file is specified, print
  on STDOUT.

OPTIONS (-o value --opt value)
   -h             Print help.
   --ref-field    Name of the field where the referent is store (REF, refname,
                  etc.). Default is REF.
   --unit-type    Type of the unit (maillon, MENTION, etc.). Default is MENTION.
   --reset        Get a new name for referent (useful if the name used in the
                  glozz file contains non standard characters).
END

sub get_cl_parameters {

   # default
   $INPUT_CORPUS = '';
   $INPUT_ANNOTATIONS = '';
   $OUTPUT_FILE = '';
   $REFNAME_FIELD = 'REF';
   $UNIT_TYPE = 'MENTION';
   $RESET_REFNAME_FIELD = '';

   my $pending = '';

   for (@ARGV) {
      print $HELP and exit if m/^(?:-h|--?help)$/;
      last if $pending and m/^-/;
      # pending
      if ($pending eq '--ref-name') {
         $REFNAME_FIELD = $_;
         $pending = '';
      } elsif ($pending eq '--unit-type') {
         $UNIT_TYPE = $_;
         $pending = '';
      # end of pending
      } elsif ($pending) {
         last;
      # options with value waiting for next element in @ARGV
      } elsif (m/^(?:--ref-name)$/) {
         $pending = '--ref-name';
      } elsif (m/^--unit-type$/) {
         $pending = '--unit-type';
      # switch (= options with no value)
      } elsif (m/^--reset$/) {
         $RESET_REFNAME_FIELD = 1;
      # end of options
      } elsif (m/^-.+/) {
         die "$0: *** option '$_' doesn't exists ***\n";
      # arguments, not options
      } elsif (!$INPUT_CORPUS and m/^(.+?\.ac)$/ and -f $1) {
         $INPUT_CORPUS = $1;
         (my $tmp = $INPUT_CORPUS) =~ s/\.ac$/.aa/;
         if (!$INPUT_ANNOTATIONS and -f $tmp) {
            $INPUT_ANNOTATIONS = $tmp;
         }
      } elsif (!$INPUT_ANNOTATIONS and m/^(.+?\.aa)$/ and -f $1) {
         $INPUT_ANNOTATIONS = $1;
         (my $tmp = $INPUT_ANNOTATIONS) =~ s/\.aa$/.ac/;
         if (!$INPUT_CORPUS and -f $tmp) {
            $INPUT_CORPUS = $tmp;
         }
      } elsif (!$OUTPUT_FILE and m/^([^-].*+)$/) {
         $OUTPUT_FILE = $1;
      } else {
         die "$0: *** bad option '$_' ***\n";
      }
   } # for

   die "$0: *** no glozz file specified ***\n"
      unless $INPUT_ANNOTATIONS and $INPUT_CORPUS;

}



########################################################################
# parser
# 
# ex:
#    'characterisation' => {
#      'featureSet' => {
#        'feature' => {
#          'gender' => {
#            'content' => 'fem'
#          },
#          'gramcat' => {
#            'content' => 'definite'
#          },
#          $REFNAME_FIELD => {},
#          'number' => {
#            'content' => 'sg'
#          }
#        }
#      },
#
# ex:
#     'characterisation' => {
#       'featureSet' => {
#         'feature' => {
#           'name' => $REFNAME_FIELD
#         }
#       },
#       'type' => $UNIT_TYPE
#     },
########################################################################

sub parse {

   my $xml = shift;
   my $corpus = shift;

   my $data = XMLin $xml, ForceArray=>'', KeyAttr => { feature=>'name' };
   #print Dumper $data; die;

   my @annotations = ();
   my @paragraphs = ();

   for my $r_unit_hash (@{$data->{unit}}) {
      if ($r_unit_hash->{characterisation}->{type} eq 'paragraph') {
         push @paragraphs, {
            start => $r_unit_hash->{positioning}->{start}->{singlePosition}->{index},
            end => $r_unit_hash->{positioning}->{end}->{singlePosition}->{index} };
      } elsif ($r_unit_hash->{characterisation}->{type} eq $UNIT_TYPE) {
         push @annotations, {
            start => $r_unit_hash->{positioning}->{start}->{singlePosition}->{index},
            end => $r_unit_hash->{positioning}->{end}->{singlePosition}->{index},
            props => $r_unit_hash->{characterisation}->{featureSet}->{feature} };
      } else {
         die "$0: *** don't know unit type '$r_unit_hash->{characterisation}->{type}' ***\n";
      }
   }

   my %chain_names = ();
   my $name_counter = 0;

   # props is of the form: { $REFNAME_FIELD=>{content=>'value'}, prop=>{content=>'value'}}
   for my $r_annotation (@annotations) {
      my %props = ();
      #print Dumper $r_annotation;
      #print substr($corpus, $r_annotation->{start}, $r_annotation->{end}-$r_annotation->{start}), "\n";
      for my $key (keys %{$r_annotation->{props}}) {
         # only one feature, which has no content:
         #     'characterisation' => {
         #       'featureSet' => {
         #         'feature' => {
         #           'name' => $REFNAME_FIELD
         #         }
         #       },
         #       'type' => $UNIT_TYPE
         #     },
         if ($key eq 'name' and not ref $r_annotation->{props}->{$key}) {
            unless ($r_annotation->{props}->{$key} eq $REFNAME_FIELD) {
               $props{$r_annotation->{props}->{$key}} = '';
            }
         # otherwise
         #     'characterisation' => {
         #       'featureSet' => {
         #         'feature' => {
         #           'gender' => {
         #             'content' => 'fem'
         #           },
         #           'gramcat' => {
         #             'content' => 'definite'
         #           },
         #           $REFNAME_FIELD => {},
         #           'number' => {
         #             'content' => 'sg'
         #           }
         #         }
         #       },
         #       'type' => $UNIT_TYPE
         #     },
         } else {
            if ($key eq $REFNAME_FIELD) {
               $r_annotation->{$REFNAME_FIELD} = $r_annotation->{props}->{$key}->{content};
            } else {
               $props{$key} = $r_annotation->{props}->{$key}->{content};
            }
         }
      }
      $r_annotation->{props} = \%props;
      $r_annotation->{$REFNAME_FIELD} = 'TODO' unless $r_annotation->{$REFNAME_FIELD};
      if ($RESET_REFNAME_FIELD) {
         if ($r_annotation->{$REFNAME_FIELD} eq 'SI') {
            $r_annotation->{$REFNAME_FIELD} = "L".$name_counter;
         } else {
            if (not exists $chain_names{$r_annotation->{$REFNAME_FIELD}}) {
               $chain_names{$r_annotation->{$REFNAME_FIELD}} = "C".$name_counter;
               $name_counter++;
            }
            $r_annotation->{$REFNAME_FIELD} = $chain_names{$r_annotation->{$REFNAME_FIELD}};
         }
      }
   }

   #print Dumper \@annotations;
   #print Dumper \@paragraphs;

   # NOTE: this is very important, otherwise nested annotations go
   # wrong!
   @annotations = sort{$a->{start}<=>$b->{start}
      or $b->{end}-$b->{start} <=> $a->{end}-$a->{start}} @annotations;

   # test that there are no overlapping annotations
   for my $i (@annotations) {
      for my $j (@annotations) {
         next if $i == $j;
         if ($i->{start} < $j->{start}
               and $j->{start} < $i->{end}
               and $i->{end} < $j->{end}) {
            $i->{end} = $j->{end};
            print sprintf "Correcting overlapping annotations: '%s' (%d,%d) and '%s' (%d,%d)\n",
               substr($corpus, $i->{start}, $i->{end}-$i->{start}),
               $i->{start}, $i->{end},
               substr($corpus, $j->{start}, $j->{end}-$j->{start}),
               $j->{start}, $j->{end};
         }
      }
   }
   for my $i (@annotations) {
      for my $j (@annotations) {
         next if $i == $j;
         if ($i->{start} < $j->{start}
               and $j->{start} < $i->{end}
               and $i->{end} < $j->{end}) {
            die sprintf "$0: overlapping annotations: '%s' (%d,%d) and '%s' (%d,%d) ***\n",
               substr($corpus, $i->{start}, $i->{end}-$i->{start}),
               $i->{start}, $i->{end},
               substr($corpus, $j->{start}, $j->{end}-$j->{start}),
               $j->{start}, $j->{end};
         }
      }
   }

   my $result = '';

   my @pending_annotations = ();
   for my $r_par (sort{$a->{start} <=> $b->{start}} @paragraphs) {
      my $par_text = substr($corpus, $r_par->{start}, $r_par->{end}-$r_par->{start});
      my $len = length $par_text;
      for (my $i= 0; $i<$len; $i++) {
         while (@pending_annotations
               and $pending_annotations[0]->{end}-$r_par->{start} == $i and $i > 0) {
            $result .= '}';
            shift @pending_annotations;
         }
         while (@annotations
               and $annotations[0]->{start}-$r_par->{start} == $i) {
            #DEBUG: my $props_string = '';
            if (exists $annotations[0]->{props}->{headpos}
                  and exists $annotations[0]->{props}->{headstring}) {
               $annotations[0]->{props}->{head} = "$annotations[0]->{props}->{headpos}: $annotations[0]->{props}->{headstring}";
               delete $annotations[0]->{props}->{headpos};
               delete $annotations[0]->{props}->{headstring};
            }
            my @props_strings = ();
            for my $key (sort keys %{$annotations[0]->{props}}) {
               my $val = $annotations[0]->{props}->{$key};
               if (not defined $val) {
                  $val = "";
               }
               push @props_strings, "$key=\"$val\"";
            }
            #my $props_string = join(',', map{"$_=\"$annotations[0]->{props}->{$_}\""} sort keys %{$annotations[0]->{props}});
            my $props_string = join(',', @props_strings);
            $props_string = ":$props_string" if $props_string;
            #print Dumper $r_annotation;
            $result .= "{$annotations[0]->{$REFNAME_FIELD}$props_string ";
            unshift @pending_annotations, shift @annotations;
         }
         $result .= substr($par_text, $i, 1);
      }
      # closing at the end of the paragraph
      while (@pending_annotations) {
         $result .= '}';
         shift @pending_annotations;
      }
      $result .= "\n\n";
   }

   if (@annotations) {
      print Dumper \@annotations;
      die "$0: *** some annotations left ***\n";
   }

   return $result;


}


########################################################################
# check comment line
########################################################################

sub check_comment_line {

   my @lines = split /\n/, shift;

   for (@lines) {
      s/^#\s*(title|source|NOTE)\s*:/#$1:/;
      if (m/^#\s*(COLOR|TOKENIZATION-TYPE|textid|part-heading)\s*:/) {
         $_ =~ s/ //g;
      }
   }

   return join("\n", @lines);

}


########################################################################
# main()
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


sub main {

   get_cl_parameters();

   if (-e $OUTPUT_FILE) {
      return '' unless (confirm_yn("File $OUTPUT_FILE exists.  Overwrite [Y/n]?", 1));
   }

   my $sacr = parse(
      read_file($INPUT_ANNOTATIONS),
      read_file($INPUT_CORPUS) );

   $sacr = check_comment_line($sacr);

   if ($OUTPUT_FILE) {
      write_file($OUTPUT_FILE, $sacr);
   } else {
      print $sacr;
   }

   return $OUTPUT_FILE;
}


main()
 and print "$0: done!\n";


