




def soundLength(file):
    """ Takes local file url, returns time in seconds. """
    import subprocess

    length_string = subprocess.check_output("""mp3info -p "%S" '{}'""".format(file), shell=True).strip('%')
    length = sum(float(x) * 60 ** i for i,x in enumerate(reversed(length_string.split(":"))))
    return length

# Mutagen proved unable to correctly parse, remove this function if soundLength
# continues to work correctly.
def mutagenLength(file):
    import mutagen
    try:
        file = mutagen.File(file)
        return file.info.length  #time in seconds
    except Exception, e:
        logger.error('Could not calculate mp3 length', exc_info=True)
        return "error"
