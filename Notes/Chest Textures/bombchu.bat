@echo off

magick -size 32x32 -depth 8 chest_base_bombchu.png ^
-channel R +level 0,31 -evaluate leftshift 11 -evaluate and 63488 +channel ^
-channel G +level 0,31 -evaluate leftshift 6 -evaluate and 1984 +channel ^
-channel B +level 0,31 -evaluate leftshift 1 -evaluate and 62 +channel ^
-channel A -evaluate and 1 +channel ^
-channel RGBA -separate +channel ^
-channel R -evaluate-sequence add  +channel ^
-depth 16 -endian MSB R:chest_base_bombchu.bin

magick -size 32x64 -depth 8 chest_front_bombchu.png ^
-channel R +level 0,31 -evaluate leftshift 11 -evaluate and 63488 +channel ^
-channel G +level 0,31 -evaluate leftshift 6 -evaluate and 1984 +channel ^
-channel B +level 0,31 -evaluate leftshift 1 -evaluate and 62 +channel ^
-channel A -evaluate and 1 +channel ^
-channel RGBA -separate +channel ^
-channel R -evaluate-sequence add  +channel ^
-depth 16 -endian MSB R:chest_front_bombchu.bin

cp chest_base_bombchu.bin ../../data/textures/chest/chest_base_bombchu_rgba16_patch.bin
cp chest_front_bombchu.bin ../../data/textures/chest/chest_front_bombchu_rgba16_patch.bin
rm chest_base_bombchu.bin
rm chest_front_bombchu.bin