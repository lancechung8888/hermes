# apkutils [![PyPI version](https://badge.fury.io/py/apkutils.svg)](https://badge.fury.io/py/apkutils) [![GitHub license](https://img.shields.io/github/license/mikusjelly/apkutils.svg)](https://github.com/mikusjelly/apkutils/blob/master/LICENSE)


A library that gets infos from APK.

### Install and Test

```
$ pip install apkutils
```

### Usage

```
$ python3 -m apkutils -h
usage: apkutils [-h] [-m] [-s] [-f] [-c] [-V] p

positional arguments:
  p              path

optional arguments:
  -h, --help     show this help message and exit
  -m             Show manifest
  -s             Show strings
  -f             Show files
  -c             Show certs
  -V, --version  show program's version number and exit

```

### Reference
- apkutils\axml from [mikusjelly/axmlparser](https://github.com/mikusjelly/axmlparser) ![Project unmaintained](https://img.shields.io/badge/project-unmaintained-red.svg)
- apkutils\dex from [google/enjarify](https://github.com/google/enjarify)

### modified by virjar
refer from https://github.com/mikusjelly/apkutils

elf模块被删除，无法使用，证书模块被删除，无法使用。因为有些依赖没有，这个项目基于python3实现的
另外，删除了PyZipFile这个class，也是由于python2中缺少部分依赖