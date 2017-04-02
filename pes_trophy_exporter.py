bl_info = {
    "name": "PES Trophy .model Exporter",
    "author": "sxsxsx, appul, juce",
    "version": (0, 9, 1),
    "blender": (2, 6, 7),
    "api": 35853,
    "location": "Properties > Scene tab",
    "description": "Converts 3D mesh models into PES Trophy .model files",
    "warning": "",
    "wiki_url": "https://implyingrigged.info/wiki/Blender",
    "tracker_url": "",
    "category": "System"}

import bpy,zlib,os
from bpy.props import *
from math import *
from mathutils import *
from struct import *
import os.path

try:
    from ctypes import windll
    has_windll = True
except:
    has_windll = False

try:
    input = raw_input
except:
    pass

if has_windll:
    STD_OUTPUT_HANDLE = -11
    stdout_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

part_list=["EXPORT"]
obname=['export']
partname=['export']
main_list=["EXPORT"]
TEMPPATH = os.path.dirname(bpy.app[4]) + os.path.sep + 'pes_temp' + os.path.sep
parentlist = [("","","")]
#e_texlist,k=[],112
e_texlist=[]
ob_id = 'EXPORT'

def uv_key(uv):
    return round(uv[0], 6), round(uv[1], 6)

class tri_wrapper(object):

    __slots__ = 'vertex_index', 'faceuv', 'offset'
    def __init__(self, vindex=(0,0,0), faceuv=None):
        self.vertex_index= vindex
        self.faceuv=faceuv
        self.offset= [0, 0, 0]

def triangles(mesh):

    tris_list=[]
    mesh.uv_textures[0].name = 'UVmap1'
    mesh.uv_textures[1].name = 'UVmap2'
    uvcount=len(mesh.uv_textures)
    mesh.update(calc_tessface=1)

    for i, f in enumerate(mesh.tessfaces):
        fv=f.vertices
        for p in range(2):
            if len(fv) == 3:
                if p == 0:
                    new_tri = tri_wrapper((fv[0], fv[1], fv[2]))
                    uvface=mesh.tessface_uv_textures['UVmap1'].data[i] if uvcount else None
                    f_uv=uvface.uv
                    t1_uv1=uv_key(f_uv[0]), uv_key(f_uv[1]), uv_key(f_uv[2])
                else:
                    uvface=mesh.tessface_uv_textures['UVmap2'].data[i] if uvcount else None
                    f_uv=uvface.uv
                    t1_uv2=(uv_key(f_uv[0]), uv_key(f_uv[1]), uv_key(f_uv[2]))
                    uv1=t1_uv1+t1_uv2
                    new_tri.faceuv=uv1
                    tris_list.append(new_tri)
            else:
                if p == 0:
                    new_tri = tri_wrapper((fv[0], fv[1], fv[2]))
                    new_tri2 = tri_wrapper((fv[0], fv[2], fv[3]))
                    uvface=mesh.tessface_uv_textures['UVmap1'].data[i] if uvcount else None
                    f_uv=uvface.uv
                    t1_uv1=uv_key(f_uv[0]), uv_key(f_uv[1]), uv_key(f_uv[2])
                    t2_uv1=uv_key(f_uv[0]), uv_key(f_uv[2]), uv_key(f_uv[3])
                else:
                    uvface=mesh.tessface_uv_textures['UVmap2'].data[i] if uvcount else None
                    f_uv=uvface.uv
                    t1_uv2=(uv_key(f_uv[0]), uv_key(f_uv[1]), uv_key(f_uv[2]))
                    t2_uv2=(uv_key(f_uv[0]), uv_key(f_uv[2]), uv_key(f_uv[3]))
                    uv1=t1_uv1+t1_uv2
                    uv2=t2_uv1+t2_uv2
                    new_tri.faceuv=uv1
                    new_tri2.faceuv=uv2
                    tris_list.append(new_tri)
                    tris_list.append(new_tri2)

    return tris_list

def remove_face_uv(verts, tris_list):

        unique_uvs= [{} for i in range(len(verts))]

        for tri in tris_list:
            for i in range(3):
                context_uv_vert= unique_uvs[tri.vertex_index[i]]
                uvkey=tri.faceuv[i],tri.faceuv[i+3]
                try:
                    offset_index, uv_3ds=context_uv_vert[uvkey]
                except:
                    offset_index=len(context_uv_vert)
                    context_uv_vert[tri.faceuv[i],tri.faceuv[i+3]]= offset_index, uvkey
                tri.offset[i]=offset_index

        vert_index = 0
        vert_array = []
        normal_array = []
        uv_array = []
        index_list = []

        for i,vert in enumerate(verts):
            index_list.append(vert_index)
            x,y,z=vert.co
            nx,ny,nz=vert.normal
            UVmap = [None] * len(unique_uvs[i])
            for ii, uv_3ds in unique_uvs[i].values():
                vert_array.append((x,y,z))
                normal_array.append((nx,ny,nz))
                UVmap[ii] = uv_3ds
            for uv_3ds in UVmap:
                uv_array.append(uv_3ds)
            vert_index += len(unique_uvs[i])
        for tri in tris_list:
            for i in range(3):
                tri.offset[i]+=index_list[tri.vertex_index[i]]
            tri.vertex_index= tri.offset

        return vert_array, normal_array, uv_array, tris_list

def zlib_comp(path):

    str_o1 = open(TEMPPATH+"unzlib_data", 'rb').read()
    str_o2 = zlib.compress(str_o1, 9)
    s1,s2=len(str_o1),len(str_o2)
    f = open(path, 'wb')
    f.write(pack("4I",0x57011000,0x53595345,s2,s1))
    f.write(str_o2),f.flush(),f.close()

def load_objs():

    global e_texlist
    part_data,objlist,texlist=[],[],[]
    scn=bpy.context.scene

    outpath = bpy.context.scene.export_path

    if bpy.ops.object.mode_set():
    	bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if ob.parent and ob.parent.name in main_list:
            if ob.hide == 0:
                ob.select = 1

    bpy.ops.object.transform_apply(location=1,rotation=1,scale=1)
    bpy.ops.object.select_all(action='DESELECT')

    print("")
    if has_windll:
        windll.kernel32.SetConsoleTextAttribute(stdout_handle, 10)
    print("Starting 3D Model Exporting...")
    if has_windll:
        windll.kernel32.SetConsoleTextAttribute(stdout_handle, 7)

    def model_header(parent):  # MODEL DATA HEADER

        s_hdr=open(TEMPPATH+"unzlib_data","wb")
        #hdr_file=open(TEMPPATH+"extras14.dll","rb")
        hdr_file=open(TEMPPATH+"extras14.bin","rb")
        data1,data2,data3=hdr_file.read(112),hdr_file.read(80),hdr_file.read(132)
        data4,data5,data6=hdr_file.read(40),hdr_file.read(24),hdr_file.read(28)
        data7,data8,data9=hdr_file.read(60),hdr_file.read(28),hdr_file.read(68)
        dat10,dat11=hdr_file.read(172),hdr_file.read(192)

        s_hdr.write(data1[:0x50])
        sublist=[ch_ob for ch_ob in parent.children if ch_ob.hide == 0]
        spc=len(sublist)

        # write orientation info
        s_hdr.write(pack("3I",12,spc+1,4))
        for i in range(spc+1):
            s_hdr.write(pack("I",12+(spc+1)*4+i*0x1c))

        matrix_size = 4*(4*3)
        oi_offs = [(spc+1)*0x1c+4]
        for i in range(1,spc+1):
            oi_offs.append((spc+1-i)*0x1c+4+matrix_size+(i-1)*0x10)

        s_hdr.write(pack("7I",0x10,1,12,2,oi_offs[0],7,1))
        for i in range(1,spc+1):
            s_hdr.write(pack("7I",0x10,1,12,2,oi_offs[i],1,1))

        s_hdr.write(pack("I",0))
        # scale and translation matrix
        s_hdr.write(pack("4f",1.0,0.0,0.0,0.0))
        s_hdr.write(pack("4f",0.0,1.0,0.0,0.0))
        s_hdr.write(pack("4f",0.0,0.0,1.0,0.0))

        for i in range(spc*4-3):
            s_hdr.write(pack("I",0))

        # done with orientation info
        k = s_hdr.tell()
        s_hdr.seek(0x28,0)
        s_hdr.write(pack("I",k-0x18))
        s_hdr.seek(k,0)

        hdr_offs,hdr_offs2=[],[]
        s_hdr.write(pack("3I",12,spc,20))
        for i in range(spc):
            s_hdr.write(pack("5I",1,255,255,0,255))
        #s_hdr.write(pack("2I",0,0))
        s_hdr.write(pack("I",0))
        hdr_offs.append(s_hdr.tell())
        for i in range(spc):
            s_hdr.write(data2)
            if i == 0:
                s_hdr.write(pack("I",0))
        hdr_offs.append(s_hdr.tell())
        for i in range(spc):
            hdr_offs2.append(s_hdr.tell())
            s_hdr.write(dat11) #(dat10) - was

        #s_hdr.seek(124,0)
        s_hdr.seek(k+12,0)
        off1,off2=hdr_offs[0]-k,hdr_offs[1]-k

        for i in range(spc):
            o1=off1+(80*i)
            o2=off2
            #kkk=136
            kkk=136+20

            if i != 0:
                o1=o1+4
                o3=hdr_offs2[i]-k
                s_hdr.write(pack("5I",1,o3,o3+kkk,0,o1))
            else:
                s_hdr.write(pack("5I",1,o2,o2+kkk,0,o1))

        s_hdr.seek(hdr_offs[0],0)
        bsize1_x,bsize1_y,bsize1_z,bsize2_x,bsize2_y,bsize2_z=[],[],[],[],[],[]
        for i in range(spc):
            s_hdr.seek(28,1)
            bsize1,bsize2=part_data[i][5][0],part_data[i][5][1]
            x1,y1,z1,w1=bsize1[0],bsize1[2],bsize1[1]*-1,0
            s_hdr.write(pack("4f",x1,y1,z1,w1)) # bound box size1
            x2,y2,z2,w2=bsize2[0],bsize2[2],bsize2[1]*-1,0
            s_hdr.write(pack("4f",x2,y2,z2,w2)) # bound box size2
            bsize1_x.append(x1),bsize1_y.append(y1),bsize1_z.append(z1),bsize2_x.append(x2),bsize2_y.append(y2),bsize2_z.append(z2)
            if i == 0:
                s_hdr.seek(24,1)
            else:
                s_hdr.seek(20,1)

        offset=s_hdr.tell()
        s_hdr.flush()
        s_hdr.seek(0,2)
        filesize=s_hdr.tell()
        p1_off=filesize-k
        s_hdr.seek(offset,0)

        for i in range(spc):
            s_hdr.seek(12,1)
            s_hdr.write(pack("I",s_hdr.tell()-k+4))
            s_hdr.seek(20,1)
            s_hdr.write(pack("5I",p1_off+part_data[i][0],2,5,part_data[i][6],0))
            s_hdr.write(pack("5I",p1_off+part_data[i][9],3,5,part_data[i][6],0))
            s_hdr.write(pack("5I",p1_off+part_data[i][10],16,5,part_data[i][6],0))
            s_hdr.write(pack("5I",p1_off+part_data[i][11],15,5,part_data[i][6],0))
            s_hdr.write(pack("5I",p1_off+part_data[i][1],7,4,part_data[i][6],0))
            s_hdr.write(pack("5I",p1_off+part_data[i][12],18,8,part_data[i][6],0))
            s_hdr.seek(12,1)
            s_hdr.write(pack("6I",p1_off+part_data[i][3],1,1,part_data[i][7]*3,0,p1_off+part_data[i][4]))

        model_data=open(TEMPPATH+'model_data.bin',"rb").read()
        s_hdr.write(model_data)
        s_hdr.flush()
        h1off=s_hdr.tell()-24
        s_hdr.write(data4)
        h2off=s_hdr.tell()-24
        s_hdr.write(pack("3I",12,spc,28))
        for i in range(spc):
            s_hdr.write(pack("7I",0,0,0,2,2,2,0))
        m1_off=s_hdr.tell()
        s_hdr.write(pack("3I",12,spc,24))
        for i in range(spc):
            s_hdr.write(data5)
        m2_off=s_hdr.tell()
        for i in range(spc):
            place = 0x50+12+(spc+1)*4+(i+1)*0x1c
            s_hdr.write(pack("4I",12,1,4, 0xffffffff - m1_off + place + 1))
        m222_off=s_hdr.tell()
        for i in range(spc):
            s_hdr.write(data6)
        m2222_off=s_hdr.tell()
        for i in range(spc):
            #s_hdr.write(data7)
            s_hdr.write(pack("3I",12,0,4))  #test
        m33_off=s_hdr.tell()

        #s_hdr.write(pack("6I",12,0,4,12,spc,4))
        s_hdr.write(pack("4I",12,1,4,16))
        s_hdr.write(pack("7sB","sk_prop".encode(),0))
        s_hdr.write(pack("3I",12,spc,4))

        m22_off=s_hdr.tell()
        m3_off = 12+(spc*4)
        for i in range(spc):
            if i == 0:
                s_hdr.write(pack("I",m3_off))
            else:
                m3_off += part_data[i-1][13]
                s_hdr.write(pack("I",m3_off))
        for i in range(spc):
            nsize=str(len(part_data[i][8]))+'sB'
            s_hdr.write(pack(nsize,part_data[i][8].encode(),0))
        #s_hdr.write(pack("H",0))  #test
        s_hdr.write(pack("I",0))  #test
        m44_off=s_hdr.tell()
        s_hdr.write(pack("3I",0,0,4))
        m4_off=s_hdr.tell()
        s_hdr.write(data8)
        m5_off=s_hdr.tell()
        s_hdr.write(data9)
        s_hdr.seek(-48,2)
        s_hdr.write(pack("8f",min(bsize1_x),min(bsize1_y),min(bsize1_z),0,max(bsize2_x),max(bsize2_y),max(bsize2_z),0))

        s_hdr.seek(m1_off+12,0)
        #a1=0xFFFFFFFF-(m1_off-125)
        a1=0xFFFFFFFF-(m1_off-(k+13))
        print("==> a1=%x" % a1)
        for i in range(spc):
            a2=a1+(i*20)
            ####a3=(m2_off-m1_off)+(i*12)
            a3=(m2_off-m1_off)+(i*16) #IMPORTANT
            a4=(m22_off-m1_off)+(i*4)
            a5=(m222_off-m1_off)+(i*28)
            #a6=(m2222_off-m1_off)+(i*60)
            a6=(m2222_off-m1_off)+(i*12)
            s_hdr.write(pack("6I",a2,a3,a5,a4,0,a6))
            print("==> a2=%x, a3=%x, a5=%x, a4=%x, 0, a6=%x" % (a2,a3,a5,a4,a6))

        s_hdr.seek(44,0)
        #s_hdr.write(pack("9I",h1off,h2off,m1_off-24,m33_off-24,m33_off-12,m5_off-24,m44_off-24,m4_off-24,m44_off))
        s_hdr.write(pack("9I",h1off,h2off,m1_off-24,m33_off-24,m33_off,m5_off-24,m44_off-24,m4_off-24,m44_off))

        s_hdr.close()
        hdr_file.close()

    def main(obj):

        vlist,uvlist,normlist,flist,binorlist,tanlist=[],[],[],[],[],[]

        bsize=obj.bound_box[3][:],obj.bound_box[5][:]
        mesh=obj.data
        mesh.update(calc_tessface=1)

        tri_list=triangles(mesh)

        if len(mesh.uv_textures):
            vlist, normlist, uvlist, tri_list = remove_face_uv(mesh.vertices, tri_list)

        for tri in tri_list:
            flist.append((tri.vertex_index))

        print("")
        print("*"*40)
        print(obj.parent.name,'->',obj.name,"is Exporting...")

        nor_off,binor_off,tan_off,uv2off = 0,0,0,0

        voff=file.tell()

        for v in range(len(vlist)):
            x,y,z=vlist[v][0],vlist[v][1],vlist[v][2]
            file.write(pack("3f",x,z,-y))

        nor_off=file.tell()

        for n in range(len(normlist)):
            nx,ny,nz=normlist[n][0],normlist[n][1]*-1,normlist[n][2]
            file.write(pack("3f",nx,nz,ny))
            normal=Vector((nx,ny*-1,nz))
            v_tangent=Vector.cross(normal,Vector((-1,0,0)))
            tanlist.append(v_tangent)
            binorlist.append(Vector.cross(v_tangent,normal))

        binor_off=file.tell()

        for b in range(len(binorlist)):
            bx,by,bz=binorlist[b][0],binorlist[b][1]*-1,binorlist[b][2]
            file.write(pack("3f",bx,bz,by))

        tan_off=file.tell()

        for t in range(len(tanlist)):
            tx,ty,tz=tanlist[t][0],tanlist[t][1]*-1,tanlist[t][2]
            file.write(pack("3f",tx,tz,ty))

        uv1off=file.tell()

        for w in range(len(vlist)):
            u1,v1=uvlist[w][0][0],uvlist[w][0][1]
            file.write(pack("2f",u1,1-v1))

        # d=0x12, f=0x8
        zero_off=file.tell()

        for _ in range(len(vlist)):
            file.write(pack("i",0))

        toff=file.tell()

        for idx in range(len(flist)):
            file.write(pack("3H",*flist[idx]))

        off1=file.tell()

        obname=obj.name

        part_data.append((voff,uv1off,uv2off,toff,off1,bsize,len(vlist),len(flist),obname,nor_off,binor_off,tan_off,zero_off,len(obj.name)+1)) #last index [13]

        return 1

    for ob in bpy.context.scene.objects:
        if ob.type == 'EMPTY' and ob.name in part_list:
            if len(ob.children) != 0:
                objlist.append(ob)

    for object in objlist:

        s=0
        file=open(TEMPPATH+'model_data.bin',"wb")

        for ob in object.children:  # script starts here
            if ob.hide == 0:
                if main(ob):
                    s=1

        file.flush(),file.close()
        if s:
            dat12=model_header(object) # add header
            part_data=[]
            pname1 = obname[part_list.index(object.name)]
            outpath2 = outpath+pname1+'.model'
            zlib_comp(outpath2)
            if scn.zlibunzlib:
                data1 = open(outpath2, 'rb')
                data1.seek(16,0)
                data2=data1.read()
                data3=zlib.decompress(data2,32)
                try:
                    out=open(outpath2,"wb")
                except(PermissionError):
                    print("")
                    self.report( {"ERROR"}, "Model file not created, run Blender as Administrator." )
                    return

                out.write(data3)
                out.flush()
                out.close()

    if os.path.exists(TEMPPATH+'unzlib_data'):
        os.remove(TEMPPATH+'unzlib_data')

    if bpy.ops.object.mode_set():
    	bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if ob.parent and ob.parent.name in main_list:
            if ob.hide == 0:
                ob.select = 1
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')

class OBJECTModelExporter(bpy.types.Panel):
    bl_label = "PES .model Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):

        global ob_id
        obj = bpy.context.active_object
        scn = bpy.context.scene
        obj_co = len(scn.objects)
        layout = self.layout

        box=layout.box()
        box.alignment='CENTER'
        if bpy.app[1][:4] != '2.67':
            box=layout.box()
            box.alignment='CENTER'
            box.label(text="This tool works with only Blender 2.67", icon='ERROR')

        row=box.row(align=0)
        col=row.column()
        col.label(text="Use this tool to convert any mesh into a PES .model",icon="INFO")
        col.label(text="This tool does not export skeleton data.",icon="INFO")
        col.label("For more information (on how to use this tool), please visit:",icon="INFO")
        row=box.row()
        row.operator("wm.url_open",text="https://implyingrigged.info/wiki/Blender",icon="URL").url="https://implyingrigged.info/wiki/Blender"

        row = layout.row()
        row.operator("exporter.operator",text="Start New Scene").opname="new_scene"

        box=layout.box()
        box.alignment='CENTER'
        row=box.row()

        vc=''
        for i in scn.statistics().split('Verts:')[1][:9]:
             if i.isdigit():
                 vc+=i
        tc=''
        for i in scn.statistics().split('Tris:')[1][:9]:
             if i.isdigit():
                 tc+=i

        row.label(text="Project Info: ",icon="INFO")
        row.operator("exporter.operator", text="Create Export Parent", icon="EMPTY_DATA").opname='parents'
        row = box.row()
        row.label(text="Total Vertices: " +vc, icon="VERTEXSEL")
        row.label(text="Total Triangles: " +tc, icon="MOD_TRIANGULATE")

        if not obj:
            box=layout.box()
            box.alignment='CENTER'
            box.label(text="There are no (active) objects in the scene.", icon="ERROR")
            box.label(text="Select any object or add new objects to the scene.")
        else:
            if obj.type != 'MESH' and obj.type != 'EMPTY':
                box=layout.box()
                box.label(text="Active object is not a valid object type.",icon="ERROR")
                box.label(text="Select a Mesh or Empty object.",icon="ERROR")
                row = layout.row()

            elif obj.type == 'EMPTY':
                if obj.name == 'EXPORT' :
                    box = layout.box()
                    box.alignment='CENTER'
                    box.label(text="All children of this parent will be exported.", icon="INFO")
                    box=layout.box()
                    box.alignment='CENTER'
                    row=box.row()
                    row.label("Export Menu:",icon="INFO")
                    row=box.row()
                    row.prop(scn,"export_path",text="")
                    if os.access(scn.export_path,0) == 0:
                        row=box.row()
                        row.label(text="Did not find export folder path, select again.",icon="ERROR")
                    row = box.row()
                    row.prop(scn,"zlibunzlib",text="Export without zlib")
                    row.operator("exporter.operator", text="Export .model File", icon="COPYDOWN").opname='export'

                else:
                    box = layout.box()
                    box.alignment='CENTER'
                    box.label(text="Incorrect parent for exports.", icon="ERROR")
                    row = layout.row()

            elif obj.type == 'MESH':
                row = box.row()
                row.label(text="Vertex Count: " +str(len(obj.data.vertices)), icon="VERTEXSEL")
                row.label(text="Face Count: " +str(len(obj.data.polygons)), icon="FACESEL")
                row = box.row()
                row.label(text="EXPORT Parent: ",icon="OUTLINER_OB_EMPTY")
                row.operator("exporter.operator",text="SET").opname='setparent'
                row.operator("exporter.operator",text="CLEAR").opname='clrparent'
                row = box.row()
                row.label(text="Object:",icon="OUTLINER_OB_MESH")
                row.prop(obj,"name",text="")
                row = col.row(); row = col.row(); ic1=ic2="ERROR"; a1=a2="None"

                if len(obj.data.uv_textures) >= 2:
                    row = box.row()
                    row.label(text="UVmap 1:",icon="POTATO")
                    row.prop(obj.data.uv_textures[0],"name",text="")
                    row = box.row()
                    row.label(text="UVmap 2:",icon="POTATO")
                    row.prop(obj.data.uv_textures[1],"name",text="")

                    if obj.data.uv_textures[0].name != 'UVmap1' or obj.data.uv_textures[1].name != 'UVmap2':
                        col=box.split(0.75)
                        col.label(text="UV map names are wrong, please click:",icon="ERROR")
                        col.operator("exporter.operator",text="Set Names").opname='set_uv'
                        row = box.row()
                        row.label(text="Make sure the first UV map is the correct one.", icon="INFO")
                else:
                    col=box.split(0.75)
                    col.label(text="Did not find 2 UV maps, add UV maps:",icon="ERROR")
                    col.operator("exporter.operator",text="Add UVs").opname='add_uv'

                box = layout.box()
                box.alignment='CENTER'

                row=box.row()
                col=row.column()
                col.label(text="Use this to transform a mesh for correct exporting as a head part.",icon="INFO")
                col.label(text="But only if the part is modelled around an import of the PES Face/Hair Mod Tool.",icon="INFO")
                row = box.row()
                row.label(text="Transform Mesh:",icon="EDIT")
                row.operator("exporter.operator", text="Transform").opname='transform'
                row = box.row()
                row.label(text="Transform Mesh Back:",icon="BACK")
                row.operator("exporter.operator", text="Undo Transform").opname='undotransform'

class OBJECTModelExporter(bpy.types.Operator):

    bl_idname = "exporter.operator"
    bl_label = "EXPORTER Operator"
    opname = StringProperty()

    def execute(self, context):

        global parentlist

        if self.opname == "set_uv":
            bpy.context.active_object.data.uv_textures[0].name="UVmap1"
            bpy.context.active_object.data.uv_textures[1].name="UVmap2"
            bpy.context.active_object.data.uv_textures.active_index = 0
            return {'FINISHED'}

        elif self.opname == "add_uv":
            uv_co=len(bpy.context.active_object.data.uv_textures)
            if uv_co == 0:
                bpy.ops.mesh.uv_texture_add('EXEC_SCREEN')
                bpy.ops.mesh.uv_texture_add('EXEC_SCREEN')
            else:
                bpy.ops.mesh.uv_texture_add('EXEC_SCREEN')
            bpy.ops.exporter.operator(opname="set_uv")
            return {'FINISHED'}

        elif self.opname == "switch_uv":
            for m_obj in bpy.context.selected_objects:
                if m_obj.data.uv_textures.active_index == 0:
                    m_obj.data.uv_textures.active_index = 1
                else:
                    m_obj.data.uv_textures.active_index = 0

            return {'FINISHED'}

        elif self.opname == "parents":
            inc_list=[]
            for i in context.scene.objects:
                if i.type == "EMPTY":
                    if i.name in main_list:
                        inc_list.append(i.name)
            for o in main_list:
                if o not in inc_list:
                    bpy.ops.object.add(type='EMPTY',location=(0,0,0))
                    ob = context.active_object
                    for i in range(3):
                        ob.lock_location[i]=1
                        ob.lock_rotation[i]=1
                        ob.lock_scale[i]=1
                    ob.name = o

            parentlist = [(ob.name,ob.name,ob.name) for i, ob in enumerate(bpy.context.scene.objects) if ob.type == 'EMPTY' if ob.name in main_list]
            parentlist.sort(reverse=0)
            bpy.types.Object.droplist = EnumProperty(name="Parent List", items=parentlist)
            self.report({"INFO"},"Export Parent has been created...")
            print("")
            return {'FINISHED'}

        elif self.opname == "setparent":
            for ob_p in bpy.context.selected_objects:
                ob_p.parent = bpy.data.objects[ob_id]
            return {'FINISHED'}

        elif self.opname == "clrparent":
            bpy.ops.object.parent_clear(type='CLEAR')
            return {'FINISHED'}

        elif self.opname == "export": #!!!!!
            load_objs()
            self.report( {"INFO"}, "Meshes converted and exported successfully." )
            print("")
            return {'FINISHED'}

        elif self.opname=="transform":
            bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            bpy.ops.transform.rotate(value=1.5708, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
            bpy.ops.transform.rotate(value=1.5708, axis=(0, 1, 0), constraint_axis=(False, True, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
            bpy.ops.transform.translate(value=(0, 0, 0.054), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            bpy.ops.transform.translate(value=(-0.039, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            return {'FINISHED'}

        elif self.opname=="undotransform":
            bpy.context.scene.cursor_location = (-0.03882, 0.0, 0.05443)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.ops.transform.translate(value=(0.039, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            bpy.ops.transform.translate(value=(0, 0, -0.054), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            bpy.ops.transform.rotate(value=-1.5708, axis=(0, 1, 0), constraint_axis=(False, True, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
            bpy.ops.transform.rotate(value=-1.5708, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
            bpy.ops.transform.resize(value=(10, 10, 10), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), texture_space=False, release_confirm=False)
            bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
            return {'FINISHED'}

        elif self.opname=="new_scene":
            bpy.ops.wm.read_homefile()
            return {'FINISHED'}



shaderlist=[("appul","appul","appul")]
bpy.types.Object.droplist = EnumProperty(name="Parent List", items=parentlist)
bpy.types.Scene.export_path = StringProperty(name=" ",subtype='DIR_PATH',default="C:\\")
bpy.types.Object.shader = EnumProperty(name="Set Shader Type", items=shaderlist, default="appul")
bpy.types.Scene.zlibunzlib = BoolProperty(name=" ",default=0,description="Set whether the saved .model will be zlibbed or not.")

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()

