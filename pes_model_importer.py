bl_info = {
    "name": "PES .model Importer / Mod Tool",
    "author": "sxsxsx, appul",
    "version": (0, 9),
    "blender": (2, 6, 7),
    "api": 35853,
    "location": "Properties > Scene tab",
    "description": "Import/Export PES .model files",
    "warning": "",
    "wiki_url": "https://implyingrigged.info/wiki/Blender",
    "tracker_url": "",
    "category": "System"}

import bpy,bmesh,zlib,os,struct
from array import array
from bpy.props import *
from struct import *

bpy.types.Scene.model_path2 = StringProperty(name="Model File",subtype='FILE_PATH',default="Select the .model file from here   --->")
bpy.types.Scene.uv_sw2 = BoolProperty(name="", default=0)
bpy.types.Scene.model_vc2 = IntProperty(name="", default=0)
modelpath,model_id = "",""
temp_folder = bpy.app[4].split('blender.exe')[0]+'pes_temp\\'
model_temp = temp_folder+"model_unzlib_temp.bin"
plist2,f_plist2,h_plist2,h_start2,f_start2,start2=[],[],[],0,0,0
pes14_voff2,pes14f_voff2,pes14h_voff2=[],[],[]

def unzlib(self,model):
    
    global modelpath

    filepath_imp=modelpath
    temp=model_temp
        
    data1 = open(filepath_imp, 'rb')
    data1.seek(16,0)
    data2=data1.read()
    data3=zlib.decompress(data2,32)
    try:
        out=open(temp,"wb")
    except(PermissionError):
        print("")
        self.report( {"ERROR"}, "Model file not created, run Blender as Administrator." )
        return
          
    out.write(data3)
    out.flush()
    out.close()
    
    return open(temp,"rb")
    
def zlib_comp(self,model):

    scn=bpy.context.scene

    filepath_exp=modelpath
    temp=model_temp
    
    exp1=open(temp, 'rb').read()
    if not scn.zlibunzlib:
        exp2=zlib.compress(exp1,9)
        s1,s2=len(exp1),len(exp2)
        exp=open(filepath_exp,"wb")
        exp.write(struct.pack("I",0x57011000))
        exp.write(struct.pack("4s","ESYS".encode()))
        exp.write(struct.pack("I",s2))
        exp.write(struct.pack("I",s1))
        exp.write(exp2)
        exp.flush()
        exp.close()
    else:
        exp=open(filepath_exp,"wb")
        exp.write(exp1)
        exp.flush()
        exp.close()


def pes14_exp(self,model):

    bpy.ops.object.select_all(action='DESELECT')
    for obj2 in bpy.data.objects:
        if obj2.name[:5] in ['Model']:
            if obj2.hide == False:
                obj2.select = True
    bpy.ops.object.transform_apply(location=1,rotation=1,scale=1)
    bpy.ops.object.select_all(action='DESELECT')

    global pes14_voff2,pes14f_voff2,pes14h_voff2

    temp=model_temp
    obname='Model'
    pes14_voff2=pes14h_voff2

    ### Export Model ###

    vc,slist=0,[0]

    for v in pes14_voff2:
        vc=vc+v[0]
        slist.append(v[0]+max(slist))
    slist.pop()

    ex14_file=open(temp,"r+b")
    oblist=[]
    for ob in bpy.data.objects:
        if ob.name[:5] == obname:
            if ob.hide == False:
                oblist.append(ob)

    for f, obj in enumerate(oblist):

        data=obj.data

        uvlayer=data.uv_layers.active.data
        vidx_list,exp_uvlist=[],[]

        for poly in data.polygons:
            for idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                if data.loops[idx].vertex_index not in vidx_list:
                    vidx_list.append(data.loops[idx].vertex_index)
                    exp_uvlist.append((uvlayer[idx].uv[0],uvlayer[idx].uv[1]))


        ex14_file.seek(pes14_voff2[f][1],0)

        for e in range(0,len(data.vertices),1):
            x,y,z=data.vertices[e].co
            ex14_file.write(pack("<3f",x,z,y*-1))

        ex14_file.seek(pes14_voff2[f][2],0)
        for s in range(0,len(data.vertices),1):
            for t in vidx_list:
                if t == s:
                    u,v = exp_uvlist[vidx_list.index(t)][0],exp_uvlist[vidx_list.index(t)][1]
                    u,v = round(u,6),round(v,6)

            ex14_file.write(struct.pack("2f",u,1-v))

    ex14_file.flush()
    ex14_file.close()

    zlib_comp(self,model)

    return 1
    
def pes14_imp(self,context,model):
    
    global pes14_voff2,pes14f_voff2,pes14h_voff2

    filepath_imp=modelpath
    dirpath=os.path.dirname(filepath_imp)+"\\"
    obname='Model'
    temp=model_temp
    texname="model_tex"
    imp_dds=[]

    hdr=open(filepath_imp,'rb').read(5)
    try:
        hdr=str(hdr,"utf-8")
        if hdr == "MODEL":
            data=open(filepath_imp,'rb').read()
            try:
                outdata=open(temp,'wb')
                outdata.write(data)
                outdata.flush()
                outdata.close()
                file=open(temp,"rb")
            except(PermissionError):
                print("")
                self.report( {"ERROR"}, "Model file not created, run Blender as Administrator." )
                return
        else:
            file=unzlib(self,model)
            if file is None:
                return
    except:
        file=unzlib(self,model)
        if file is None:
            return
    
    def create_mesh(obname,q):
        
        mesh = bpy.data.meshes.new(obname)
        mesh.from_pydata(vlist, edges, flist)
            
        from bpy_extras import object_utils
       
        object_utils.object_data_add(bpy.context, mesh, operator=None)
        ac_ob=bpy.context.active_object 
        ac_ob.location=0,0,0
        ac_ob.show_all_edges=1
        ac_ob.show_wire=0
        me=ac_ob.data
        bpy.ops.mesh.uv_texture_add('EXEC_SCREEN')
        bm = bmesh.new() 
        bm.from_mesh(me) 
        uv_layer = bm.loops.layers.uv.verify()
        
        for f in range(len(bm.faces)):
            for i in range(len(bm.faces[f].loops)):
                fuv=bm.faces[f].loops[i][uv_layer]
                fuv.uv = uvlist[flist[f][i]]
                
        bm.to_mesh(me)
        bm.free()

        return ac_ob
    
    file.seek(40,0)
    k=unpack("I",file.read(4))[0]
    if k > 0x01000000:
        print("")
        self.report( {"ERROR"}, "This is not a PC game file. Supports only PC game version." )
        return
    
    offlist1,offlist2=[],[]
    vlist,flist,edges,uvlist=[],[],[],[]

    k+=24
    file.seek(k,0)
    
    zz,spc,_len=unpack("3I",file.read(12))
    
    for r in range(spc):
        _,x2,x3,_,_=unpack("5I",file.read(20))
        offlist1.append(x2)
        offlist2.append(x3)
        print("offlist1: added: %x" % x2)
        print("offlist2: added: %x" % x3)
        
    m=0
    for q in range(spc):
        tlist=[]
        file.seek(offlist1[q]+k+20,0)
        
        vert_elements,d,f,r= unpack("4I",file.read(16))
        for e in range(vert_elements):
            offset,d,f,vc,r=unpack("5I",file.read(20))
            print("offset=%x, d=%x, f=%x, vc=%x, r=%x" % (offset,d,f,vc,r))
            if d == 2 and f == 5:
                voff=offset
                v_count=vc
                print("==> voff=%x, v_count=%x" % (voff,v_count))
            elif d == 7 and f == 4:
                uvoff=offset     
                print("==> uvoff=%x" % uvoff)
        
        file.seek(offlist2[q]+12+k,0)
        toff,d,f,t_count=unpack("4I",file.read(16))
        print("toff=%x, t_count=%x" % (toff, t_count))
        
        vlist,uvlist,flist=[],[],[]
         
        file.seek(voff+k,0)
        for i in range(v_count):
            x,y,z=unpack("3f",file.read(12))
            vlist.append((x,z*-1,y))
        
        pes14_voff2.append((v_count,voff+k,uvoff+k))
        file.seek(uvoff+k,0)
        
        for w in range(v_count):
            u,v=unpack("2f",file.read(8))
            uvlist.append((u,1-v))
           
        file.seek(toff+k,0)
        
        for a in range(t_count):
            t1=unpack("H",file.read(2))[0]
            tlist.append(t1+m)
          
        for p in range(0,(len(tlist)-2),3):
            flist.append((tlist[p+0],tlist[p+1],tlist[p+2]))
           
        if q < spc:
            m=0
            obname="Model"
            obname=obname+"_"+str(q)
            ac_ob=create_mesh(obname,q)
            if q < (spc-1):
                add_mat(ac_ob,model)
        else:
            m=max(tlist)+1
        
    pes14h_voff2=pes14_voff2
    
    add_mat(ac_ob,model)
      
    file.flush()
    file.close()  

def add_mat(ac_ob,model):
    
    obname="Model"
    texname="model_tex"
    
    ### Add Material ###
    if len(bpy.data.materials) == 0:
        bpy.ops.material.new()
    matname='material'
    bpy.data.materials[0].name=matname
    bpy.data.materials[matname].use_face_texture=1 
    bpy.data.materials[matname].game_settings.use_backface_culling = 0
    bpy.data.materials[matname].game_settings.alpha_blend='CLIP'
    bpy.data.materials[matname].use_face_texture_alpha=1
    
    bpy.context.active_object.data.materials.append(bpy.data.materials[matname])
    bpy.context.scene.game_settings.material_mode = 'MULTITEXTURE'
    bpy.context.scene.uv_sw2 = 0
    bpy.context.scene.model_vc2 = len(ac_ob.data.vertices)

class Model_Importer_PA(bpy.types.Panel):
    bl_label = "PES .model Importer / Mod Tool"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    def draw(self, context):
        
        global modelpath,model_id
        
        obj = bpy.context.active_object
        scn = bpy.context.scene
        layout = self.layout
        if obj and obj.type == 'MESH':
            if obj.active_material:
                game = obj.active_material.game_settings
         
        box=layout.box()
        col=box.column()
        col.label("Use this tool to import PES .model files",icon="INFO")
        col.label("Only export .model files that you imported with this tool.",icon="INFO")
        col.label("For more information (on how to use this tool), please visit:",icon="INFO")
        row=box.row()
        row.operator("wm.url_open",text="https://implyingrigged.info/wiki/Blender",icon="URL").url="https://implyingrigged.info/wiki/Blender"

        row = layout.row()
        row.operator("model.operator",text="Start New Scene").face_opname="new_scene"

        ## Model Panel
        box=layout.box()
        row=box.row(align=1)
        row.label(text=".model file:")
        box.prop(scn,"model_path2",text="")
        modelpath=bpy.path.abspath(scn.model_path2)
            
        model_id=bpy.path.display_name_from_filepath(modelpath)+'.model'

                
        row=box.row(align=0)
        if modelpath[-6:] not in ['.model']:
            row.enabled=0
        row.operator("model.operator",text="Import .model").face_opname="import_model"
        row.operator("model.operator",text="Export .model").face_opname="export_model"
        row=box.row(align=0)
        row.prop(scn,"zlibunzlib",text="Export without zlib")

        for i in range(2):
            row = layout.row()
        
class Model_Importer_OP(bpy.types.Operator):
    
    bl_idname = "model.operator"
    bl_label = "Add Model"
    
    face_opname = StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.mode=="OBJECT"
    
    def execute(self, context):
        
        global plist2,modelpath,model_id,pes14_voff2
        scn=bpy.context.scene

        if self.face_opname=="import_model":
            if os.access(modelpath,0) == 1:
                model="model"
                plist2,pes14_voff2,pes14h_voff2=[],[],[]
                pes14_imp(self, context, model)
                return {'FINISHED'}
                
            else:
                print("")
                self.report( {"ERROR"}, "File not found: No selected file, wrong filepath or file does not exist." )
                return {'FINISHED'}
        
        elif self.face_opname=="export_model":
            model='model'
            run=pes14_exp(self,model)
            str=" "
            if run:
                print("")
                self.report( {"INFO"}, "Model"+str+"exported successfully." )
                print("appul")
                print("")
                return {'FINISHED'}
            else:
                print("")
                return {'FINISHED'}

        elif self.face_opname=="new_scene":
            bpy.ops.wm.read_homefile()
            return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
