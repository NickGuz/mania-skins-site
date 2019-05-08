from flask import redirect, render_template
from requests import get
from PIL import Image
import os.path
import os
import shutil
import sqlite3
import sys
import zipfile


class SkinImage:
    def __init__(self, root, file, x, y):
        self.x = x
        self.y = y

        # file names in skin.ini aren't always same case, so check both
        try:
            self.image = Image.open(f"{root}/{file}")
        except:
            try:
                self.image = Image.open(f"{root}/{file.lower()}")
            except:
                print(f"Failed to open image {root}/{file}")

    def resize(self, num):
        width, height = self.image.size
        new_width = num
        new_height = new_width * height / width
        self.image = self.image.resize((int(new_width), int(new_height)), Image.ANTIALIAS)
        return

    def get_image(self):
        return self.image

    def get_height(self):
        return self.image.height

    def copy_size(self, other):
        self.image = self.image.resize(other.size, Image.ANTIALIAS)


def sql_execute(query, t):
    conn = sqlite3.connect("mania.db")
    db = conn.cursor()
    db.execute(query, t)
    data = db.fetchall()

    # no need to commit if just a select query
    if query.split(' ', 1)[0] != "SELECT":
        conn.commit()

    db.close()
    return data


def alert_page(message):
    return render_template("alert.html", alertText=message)


def download_skin(url, name):
    # open url and write data to new file
    with open(f"skins/{name}.osk", "wb") as file:
        response = get(url)
        file.write(response.content)

    # create zip of file, create thumbnail, then delete zip
    with open(f"skins/{name}.zip", "wb") as zip_file:
        response = get(url)
        zip_file.write(response.content)

    with zipfile.ZipFile(f"skins/{name}.zip", "r") as zip_ref:
        zip_ref.extractall(f"skins/{name}")

    create_thumbnail(f"skins/{name}", name)
    os.remove(f"skins/{name}.zip")
    shutil.rmtree(f"skins/{name}")

    return f"/static/thumbnails/{name}"


def create_thumbnail(skin_dir, skin_name):
    # define constants for image size
    FINAL_HEIGHT = 600
    FINAL_WIDTH = 400

    # init some stuff
    bar_outer = None
    bar_inner = None
    receptor_outer = None
    receptor_inner = None
    stage_hint = None
    notes = []
    receptors = []

    for root, dirs, files in os.walk(skin_dir):
        for file in files:

            # check to see if mania note imgs in base skin folder
            if str(file) == "mania-note1.png":
                bar_outer = SkinImage(root, str(file), 0, 0)
            elif str(file) == "mania-note2.png":
                bar_inner = SkinImage(root, str(file), 0, 0)
            elif str(file) == "mania-key1.png":
                receptor_outer = SkinImage(root, str(file), 0, 0)
            elif str(file) == "mania-key2.png":
                receptor_inner = SkinImage(root, str(file), 0, 0)
            elif str(file) == "mania-stage-hint.png":
                stage_hint = SkinImage(root, str(file), 0, 0)

            # get note img locations from skin.ini if not in base folder
            if str(file) == "skin.ini":
                skin_ini = (f"{root}/{file}")

                # certain ini files seem to contain characters that break python so ignore them
                # or use try except
                with open(skin_ini, "r+", encoding="utf-8", errors="ignore") as ini:
                    lines = ini.readlines()
                    ini.seek(0)

                    # get line number "keys: 4" is on and start new loop from there, ending at "keys: 5"
                    for position, line in enumerate(lines):
                        if "Keys: 4" in line:
                            line_pos = position + 1  

                    try:
                        for line in lines[line_pos:]:
                            # break if no longer in 4key section
                            if "Keys:" in line:
                                break

                            # get receptor images
                            if "KeyImage0:" in line:
                                left_receptor = SkinImage(root, fix_backslashes(line[11:]), 0, 0)
                                receptors.append(left_receptor)

                            if "KeyImage1:" in line:
                                down_receptor = SkinImage(root, fix_backslashes(line[11:]), 0, 0)
                                receptors.append(down_receptor)

                            if "KeyImage2:" in line:
                                up_receptor = SkinImage(root, fix_backslashes(line[11:]), 0, 0)
                                receptors.append(up_receptor)

                            if "KeyImage3:" in line:
                                right_receptor = SkinImage(root, fix_backslashes(line[11:]), 0, 0)
                                receptors.append(right_receptor)

                            # get note images
                            if "NoteImage0:" in line:
                                left_note = SkinImage(root, fix_backslashes(line[12:]), 0, 0)
                                notes.append(left_note)

                            if "NoteImage1:" in line:
                                up_note = SkinImage(root, fix_backslashes(line[12:]), 0, 0)
                                notes.append(up_note)

                            if "NoteImage2:" in line:
                                down_note = SkinImage(root, fix_backslashes(line[12:]), 0, 0)
                                notes.append(down_note)

                            if "NoteImage3:" in line:
                                right_note = SkinImage(root, fix_backslashes(line[12:]), 0, 0)
                                notes.append(right_note)

                    except:
                        # if any of the above fails it's probably a skin with no mania elements
                        print("Error reading mania elements")
                            
        # don't allow to go in other folders
        break

    # create blank final image
    final_img = Image.new("RGBA", (400, 600), color="black")    
    
    # if we have info from the ini
    try:
        for note in notes:
            note.resize(FINAL_WIDTH / 4)

        for receptor in receptors:
            receptor.resize(FINAL_WIDTH / 4)

        # set some vals
        receptor_height = (FINAL_HEIGHT - 10) - receptors[0].get_height()
        vals = [(0, 350), (100, 300), (200, 250), (300, 200)]
        rval = 0

        # paste into final image
        for i, note in enumerate(notes):
            final_img.paste(receptors[i].get_image(), (rval, receptor_height), receptors[i].get_image())
            final_img.paste(note.get_image(), vals[i], note.get_image())
            rval = rval + 100

    # should fall into this if no mania fields found in skin.ini
    except:
        # resize bars and receptors
        bar_inner.resize(FINAL_WIDTH / 4)
        bar_outer.resize(FINAL_WIDTH / 4)
        receptor_inner.resize(FINAL_WIDTH / 4)
        receptor_outer.resize(FINAL_WIDTH / 4)
        stage_hint.resize(FINAL_WIDTH)

        # check and fix if receptors are not same size
        # this seems to happen with bar skins sometimes
        if receptor_outer.get_image().size != receptor_inner.get_image().size:
            receptor_outer.copy_size(receptor_inner.get_image())

        # paste everything into final image
        receptor_height = FINAL_HEIGHT - receptor_outer.get_height()
        final_img.paste(bar_outer.get_image(), (0, 450), bar_outer.get_image())    # paste bars
        final_img.paste(bar_inner.get_image(), (100, 400), bar_inner.get_image())
        final_img.paste(bar_inner.get_image(), (200, 350), bar_inner.get_image())
        final_img.paste(bar_outer.get_image(), (300, 300), bar_outer.get_image())
        final_img.paste(receptor_outer.get_image(), (0, receptor_height), receptor_outer.get_image())    # paste receptors
        final_img.paste(receptor_inner.get_image(), (100, receptor_height), receptor_inner.get_image())
        final_img.paste(receptor_inner.get_image(), (200, receptor_height), receptor_inner.get_image())
        final_img.paste(receptor_outer.get_image(), (300, receptor_height), receptor_outer.get_image())
        final_img.paste(stage_hint.get_image(), (0, FINAL_HEIGHT - stage_hint.get_height()), stage_hint.get_image())    # paste stage hint

    # save final image
    final_img.save(f"static/thumbnails/{skin_name}", "PNG")
    return


# function to convert backslashes in file names to forward slashes
def fix_backslashes(file_name):
    new_list = []
    i = 0
    for pos, char in enumerate(file_name):
        if char == "\\":
            new_list.append(file_name[i:pos])
            i = pos + 1
        elif char == "\n":
            new_list.append(file_name[i:-1])

    file_name = "/".join(new_list)
    return file_name + ".png"


# for testing purposes
def main(argv):
    create_thumbnail(argv, "test")
    return

if __name__ == "__main__":
    main(sys.argv[1])