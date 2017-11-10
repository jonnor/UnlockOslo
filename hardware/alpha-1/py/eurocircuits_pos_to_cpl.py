#!/usr/bin/env python
from __future__ import print_function

import argparse
import sys
import re

parser = argparse.ArgumentParser(description='KiCAD position to EuroCircuits CPL converter')

parser.add_argument('--top',
                    required=False,
                    dest='top',
                    action='store',
                    help='The foo-top.pos file')

parser.add_argument('--bottom',
                    required=False,
                    dest='bottom',
                    action='store',
                    help='The foo-bottom.pos file')

parser.add_argument('--output',
                    required=False,
                    dest='output',
                    action='store',
                    help='Write CPL to file')

class PlacementsFile():
  def __init__(self, unit, angle, placements):
    self.unit = unit
    self.angle = angle
    self.placements = placements

class Placement():
  def __init__(self, reference, value, package, pos_x, pos_y, rotation, side):
    self.reference = reference
    self.value = value
    self.package = package
    self.pos_x = pos_x
    self.pos_y = pos_y
    self.rotation = rotation
    self.side = side

def process_file(file):
  print("Processing {}".format(file))
  with open(file) as f:
    ps = process_lines(f.readlines())
    if ps:
        print("Loaded {} placements, using unit = {} and angle = {}".format(len(ps.placements), ps.unit, ps.angle))
    return ps

def process_lines(lines):
  unit_re = re.compile("^#.*Unit = ([^ ,.]+).*$")
  angle_re = re.compile("^#.*Angle = ([^ ,.]+).*$")
  ref_re = re.compile("^# Ref")
  idx_val = None
  idx_package = None
  out = []
  for l in lines:
    l = l.strip()
    match = unit_re.search(l)
    if match:
      unit = match.group(1)
    match = angle_re.search(l)
    if match:
      angle = match.group(1)
    match = ref_re.search(l)
    if match:
      idx_val = l.find("Val")
      idx_package = l.find("Package")
    if not l.startswith('#'):
      if idx_val < 0 or idx_package < 0:
        print("Have not found line describing headers yet")
        return None
      ref = l[0:idx_val].strip()
      val = l[idx_val:idx_package].strip()
      l = l[idx_package:]
      parts = [l for l in l.split(" ") if len(l) > 0]
      if len(parts) != 5:
        continue
      out.append(Placement(ref, val, parts[0], parts[1], parts[2], parts[3], parts[4]))

  return PlacementsFile(unit, angle, out)

def to_cpl(out, top = None, bottom = None):
  print("Reference,Center X,Center Y,Rotation,Side", file=out)

  def write(p):
    print("{},{},{},{},{}".format(p.reference, p.pos_x, p.pos_y, p.rotation, p.side), file=out)

  placements = []
  if top is not None:
    placements.extend(top.placements)
  if bottom is not None:
    placements.extend(bottom.placements)

  for p in placements:
    write(p)

def main():
  args = parser.parse_args()

  positions = []
  if args.top is not None:
    top = process_file(args.top)
    if not top:
      sys.exit(1)

  if args.bottom is not None:
    bottom = process_file(args.bottom)

  if args.output:
    with open(args.output, "w") as f:
      to_cpl(f, top, bottom)
  else:
    to_cpl(sys.stdout, top, bottom)

if __name__ == '__main__':
  main()
