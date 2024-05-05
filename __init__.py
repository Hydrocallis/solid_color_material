bl_info = {
    "name": "Solid Color Material",
    "author": "KSYN",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > UI > KSYN",
    "description": "Create simple color textured materials for selected objects",
    "warning": "",
    "wiki_url": "",
    "category": "Material",
}

preview_collections = {}

import bpy,bmesh,subprocess,os
from bpy.props import FloatVectorProperty, FloatProperty,BoolProperty,StringProperty,IntProperty
import bpy.utils.previews
from bpy.types import (
                        Panel,
                        Menu,
                        Operator,
                        PropertyGroup,
                        AddonPreferences,
                        )

def reload_unity_modules(name, debug=False):
    import os
    import importlib
   
    utils_modules = sorted([name[:-3] for name in os.listdir(os.path.join(__path__[0], "utils")) if name.endswith('.py')])

    for module in utils_modules:
        impline = "from . utils import %s" % (module)
        if debug == True:
            print("##UTILS RELOAD %s" % (".".join([name] + ['utils'] + [module])))

        exec(impline)
        importlib.reload(eval(module))

if 'bpy' in locals():
    reload_unity_modules(bl_info['name'])

from .utils.get_translang import get_translang

class KSYNSolidColorMataddonPreferences(AddonPreferences):

    bl_idname = __package__

    file_save_folder_name: StringProperty(
        name=get_translang("Name of the folder to be created when not specified.","指定してない時に作成されるフォルダの名前"),
        default="Texture",
        # subtype='FILE_PATH',
    )# type: ignore
    filepath: StringProperty(
        name=get_translang("File location","ファイルの場所"),
        subtype='FILE_PATH',
    )# type: ignore
    move_file_location: BoolProperty(
        name=get_translang("Change the location of the texture storage","テクスチャの保存場所を変える"),
        default=False,
    )# type: ignore

    def draw(self, context):
        layout = self.layout
        addon_prefs = bpy.context.preferences.addons[__name__].preferences
        layout.prop(addon_prefs, "move_file_location")
        if addon_prefs.move_file_location:
            layout.prop(addon_prefs, "filepath", )
        elif not addon_prefs.move_file_location:
            layout.prop(addon_prefs, "file_save_folder_name")

class KSYNSCM_OpenAddonPreferences(bpy.types.Operator):
    bl_idname = "ksynscm.open_addonpreferences"
    bl_label = "Open Addon Preferences"

    cmd: bpy.props.StringProperty(default="", options={'HIDDEN'}) # type: ignore

    def execute(self, context):

        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[__package__].preferences

        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        preferences.active_section = 'ADDONS'
        bpy.ops.preferences.addon_expand(module = __package__)
        bpy.ops.preferences.addon_show(module = __package__)

        return {'FINISHED'}
# アイコン呼び出しクラス
class RegisterIcons():
    # アイコンフォルダがなかったら作る つまり、事前チェックなのだ   
    @classmethod
    def create_folder_if_none(cls ,texture_dir):
        # テクスチャを保存
        if not os.path.exists(texture_dir):
            os.makedirs(texture_dir)

    @classmethod
    def make_filepath(cls):
        datapath=os.path.dirname(bpy.data.filepath)
        addon_prefs = bpy.context.preferences.addons[__name__].preferences

        if addon_prefs.move_file_location:
            icon_dir=addon_prefs.filepath
        else:
             icon_dir = os.path.join(datapath, addon_prefs.file_save_folder_name)
        return icon_dir
    
    # アイコンの辞書を作成する関数
    def create_icon_dictionary(self, icon_folder):
        icons = {}
        self.create_folder_if_none(icon_folder)

        for filename in os.listdir(icon_folder):
            if filename.endswith(".png"):  # pngファイルのみを対象にする
                icon_name = os.path.splitext(filename)[0]  # 拡張子を除いたファイル名を取得
                icon_path = os.path.join(icon_folder, filename)  # アイコンのフルパス
                icons[icon_name] = icon_path
        return icons

    # プレビューコレクションを登録する関数
    def register_icons(self):
        icon_dir=self.make_filepath()
        icon_dictionary = self.create_icon_dictionary(icon_dir)
        import bpy.utils.previews
        pcoll = bpy.utils.previews.new()
        
        for key, value in icon_dictionary.items():
            pcoll.load(key, value, 'IMAGE')
        preview_collections["main"] = pcoll
        bpy.types.Scene.custom_icons = preview_collections
        bpy.types.Scene.custom_icons_path = icon_dictionary
    # プレビューコレクションを削除する関数
    def unregister_icons(self):
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()
        try:
            del bpy.types.Scene.custom_icons
            del bpy.types.Scene.custom_icons_path
        except:
            pass
    # リフレッシュ関数
    def refresh(self):
        self.unregister_icons()
        self.register_icons()
# リフレッシュオペレーター
class KsynSolidColorOBJECT_OT_RefreshIcons(bpy.types.Operator):
    bl_idname = "object.refresh_icons"
    bl_label = "Refresh Icons"
    bl_description = "Refresh icons from the icon directory"
    
    cmd: bpy.props.StringProperty(default='', options={'HIDDEN'}) # type: ignore 

    def string_to_tuple(self,text):
        # 不要な文字を取り除く
        text = text.replace('(', '').replace(')', '')
        # カンマで分割してリストにする
        items = text.split(',')
        # ダブルクォーテーションを取り除き、各要素をタプルに変換する
        tuple_result = tuple(item.strip().strip('"') for item in items)
        return tuple_result

            
    def execute(self, context):
        tuple_result = self.string_to_tuple(self.cmd)
        # print("###tuple_result",type(tuple_result))

        if tuple_result[0]=="fol_open":
             subprocess.run('explorer /select,{}'.format(tuple_result[1]))
        else:
            RegisterIcons().refresh()
        return {'FINISHED'}
# カスタムアイコンのパネルを定義
class KsynSolidColorCustomIconPanel(bpy.types.Panel):
    bl_idname = "KSYNOBJECT_PT_custom_icon_panel"
    bl_label = "Custom Icon Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "KSYN"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        # 現在のファイルパスを取得
        filepath = bpy.data.filepath

        # ファイルパスが空でない場合、ファイルが保存されていることを表示
        if filepath:
            # layout.label(text="File is saved.")
            self.draw_icon_panels(context,row,layout)
        else:
            layout.label(text="File is not saved.")



    def draw_icon_panels(self, context,row,layout):
        row.operator("object.refresh_icons").cmd="(refresh,_)"
    
        # アイコンの辞書からアイコンを取得して表示
        # bpy.context.scene が存在し、かつ custom_icons_path 属性があるかを確認
        if hasattr(bpy.context.scene, "custom_icons_path"):
            
    
            texture_prop = context.scene.ksyn_solid_texture_prop

            layout.prop(texture_prop, "look_path")
            row = layout.row()

            # 実行したい処理をここに記述する
            grid_flow = layout.grid_flow(columns=5, even_columns=False, even_rows=False,align=True)

            for index, key in enumerate(bpy.context.scene.custom_icons["main"].keys()):
                if texture_prop.look_path:
                    row = layout.row()
                else:
                    row =grid_flow
                row.operator("object.create_texture",
                             text = f'{index} {bpy.context.scene.custom_icons_path[key]}' if texture_prop.look_path else "", 
                icon_value=bpy.context.scene.custom_icons["main"][key].icon_id).cmd = key
                if texture_prop.look_path:
                    row.operator("object.refresh_icons",icon="FILEBROWSER",text="").cmd = f"(fol_open,{bpy.context.scene.custom_icons_path[key]})"
        else:
            pass

class KSYN_TextureProperties(bpy.types.PropertyGroup):
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR_GAMMA',
        description="Color of the texture",
        default=(1, 1, 1, 1),
        size=4,
        min=0, max=1,
    ) # type: ignore
    look_path:bpy.props.BoolProperty(name="look path",default=False) # type: ignore
    use_same_rgb_mat:bpy.props.BoolProperty(name=get_translang("Use the same color material if available.","同じ色のマテリアルがあればそれを使用する"),default=True) # type: ignore
    useobjectname:bpy.props.BoolProperty(name=get_translang("Use the name of the active object as the material","アクティブなオブジェクト名をマテリアルに使う"),default=False) # type: ignore
    input_node_alpha:bpy.props.BoolProperty(name=get_translang("Connecting an image to an alpha node","画像をアルファノードにつなぐ"),default=False) # type: ignore
    
class KSYN_TexturePanel(bpy.types.Panel):
    bl_label = "Solid Color Material"
    bl_idname = "KSYNOBJECT_PT_texture_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KSYN"

    def draw(self, context):
        layout = self.layout
        texture_prop = context.scene.ksyn_solid_texture_prop
        # TexturePropertiesを取得
        layout.operator("ksynscm.open_addonpreferences")
        # Colorを表示
        layout.prop(texture_prop, "use_same_rgb_mat")
        layout.prop(texture_prop, "useobjectname")
        layout.prop(texture_prop, "input_node_alpha")
        layout.prop(texture_prop, "color")
        layout.operator("object.create_texture").cmd = "new_mat"

        self.draw_material_slots(context)

    def draw_material_slots(self, context):
        layout = self.layout
        ob = context.object
        if ob:
            is_sortable = len(ob.material_slots) > 1
            rows = 3
            if is_sortable:
                rows = 5

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.separator()

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row()

        if ob:
            row.template_ID(ob, "active_material", new="material.new")

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")
        
class KSYN_CreateTextureOperator(bpy.types.Operator):
    bl_idname = "object.create_texture"
    bl_label = "Create Texture"

    cmd: bpy.props.StringProperty(default="", options={'HIDDEN'}) # type: ignore
        
    def assign_material_to_selected_faces(self, obj, addmat):
        # Retrieve the active object and the selected faces
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        selected_faces = [f for f in bm.faces if f.select]

        # Create a new material and assign it to the selected faces
        me.materials.append(addmat)
        for face in selected_faces:
            face.material_index = len(me.materials) - 1

        # Update the mesh and deselect everything
        bmesh.update_edit_mesh(me)
        
    def add_material_to_object(self, obj, addmat):
        if bpy.context.mode == 'EDIT_MESH':
            # If in edit mode, call the  function
            import bmesh
            bm = bmesh.from_edit_mesh(obj.data)
            selected_faces = [f for f in bm.faces if f.select]
            if selected_faces:
                self.assign_material_to_selected_faces(obj, addmat)
        else:
            # 選択したオブジェクトのマテリアルを削除
            # 選択したオブジェクトのうちメッシュオブジェクトとカーブオブジェクトのマテリアルを削除
            for obj in bpy.context.selected_objects:
                if obj.type in ['MESH', 'CURVE']:
                    obj.data.materials.clear()
                    # Add new material
                    obj.data.materials.append(addmat)
  
    def execute(self, context):
        texture_prop = bpy.context.scene.ksyn_solid_texture_prop

        if self.cmd == "new_mat":
            # 同じマテリアル名があるかどうか調べる
            if texture_prop.use_same_rgb_mat:
                addmat=bpy.data.materials.get(self.material_name)
                # なければ追加
                if not addmat:
                    addmat = bpy.data.materials.new(name=self.material_name)

            elif not texture_prop.use_same_rgb_mat:
                addmat = bpy.data.materials.new(name=self.material_name)
            else:
                print("texture_prop.use_same_rgb_mat not found")

            for obj in bpy.context.selected_objects:
                self.add_material_to_object(obj, addmat)
                self.add_material(addmat)

            self.save_tex()

            RegisterIcons().refresh()
        else:
      
            addmat=bpy.data.materials.get(self.cmd)
            if addmat==None:
                # マテリアルが存在しないカラーテクスチャのマテリアルを作成します。
                addmat = bpy.data.materials.new(name=self.material_name)
                self.add_material(addmat, use_imagepath=True,image_name=self.cmd)
                pass
                
            for obj in bpy.context.selected_objects:
                self.add_material_to_object(obj, addmat)
    
        return {'FINISHED'}

    def add_material(self, addmat,use_imagepath=False, image_name=""):
        # ノードを設定
        addmat.use_nodes = True
        nodes = addmat.node_tree.nodes
        links = addmat.node_tree.links

        # プリンシプルBSDFノードを追加 or 取得
        principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
        if principled_node is None:
            principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled_node.location = 0,0

        # イメージテクスチャを追加
        
        self.image_node = nodes.new(type='ShaderNodeTexImage')
        self.image_node.location = -400,0

        # イメージパスを使わない場合
        if not use_imagepath:
            self.image_node.image = bpy.data.images.new(name = self.texturename, width=1, height=1, alpha=True)
            self.image_node.image.pixels[:] = self.pixels

        # イメージパスを使う場合
        else:
            image = bpy.data.images.load(bpy.context.scene.custom_icons_path[image_name])

            self.image_node.image= image

        self.links_nodes(links, principled_node)
        self.chnage_method(addmat)

    def links_nodes(self,links, principled_node):
        texture_prop = bpy.context.scene.ksyn_solid_texture_prop

        # テクスチャとプリンシプルBSDFノードを接続
        if not any(link.to_node == principled_node for link in self.image_node.outputs[0].links):
            links.new(self.image_node.outputs[0], principled_node.inputs[0])
            if texture_prop.input_node_alpha:
                links.new(self.image_node.outputs[0], principled_node.inputs['Alpha'])

    def chnage_method(self, addmat):
        
        addmat.blend_method='HASHED'
        addmat.shadow_method='HASHED'

    def save_tex(self):
        RegisterIcons.create_folder_if_none(self.texture_dir)
        texture_name = self.texturename
        texture_path = os.path.join(self.texture_dir, texture_name + ".png")
        self.image_node.image.file_format = 'PNG'
        self.image_node.image.filepath_raw = texture_path
        self.image_node.image.save()
        self.report({'INFO'}, "Save Texture " + texture_path)
        
    def draw(self, context):
        texture_prop = bpy.context.scene.ksyn_solid_texture_prop
        self.layout.label(text="Color")
        self.layout.prop(texture_prop, "color")

    def invoke(self, context, event):
        # ファイルのパスを取得
        texture_prop = bpy.context.scene.ksyn_solid_texture_prop

        red = texture_prop.color[0]
        green = texture_prop.color[1]
        blue = texture_prop.color[2]
        alpha = texture_prop.color[3]
        piccoloer_str = "_{:.2f}_{:.2f}_{:.2f}_{:.2f}".format(red, green, blue, alpha)
        self.pixels = [red, green, blue, alpha]
        # 新しい色のテクスチャを作成
        if self.cmd=="new_mat":
            # prifixである色番号の手前に付ける名前
            if not texture_prop.useobjectname:
                mat_option_name="ColorMaterial"
            #　オブジェクトネームをprifixに使う
            else:
                mat_option_name=bpy.context.object.name
            material_name = f"{mat_option_name}" + piccoloer_str 
            self.material_name = material_name
            self.texturename = material_name
        # この場合はフォルダに入っるテクスチャ名が使用される
        else:
            self.material_name = self.cmd 
            self.texturename = self.cmd 

        # ファイルの保存先の分岐※クラスメソッド
        self.texture_dir = RegisterIcons.make_filepath()

        return self.execute(context)

classes = [
    KSYNSolidColorMataddonPreferences,
    KSYNSCM_OpenAddonPreferences,
    KSYN_CreateTextureOperator,
    KSYN_TextureProperties,
    KSYN_TexturePanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.ksyn_solid_texture_prop = bpy.props.PointerProperty(type=KSYN_TextureProperties)

    # register_icons()
    bpy.utils.register_class(KsynSolidColorCustomIconPanel)
    bpy.utils.register_class(KsynSolidColorOBJECT_OT_RefreshIcons)

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


    
    del bpy.types.Scene.ksyn_solid_texture_prop

    # unregister_icons()
    bpy.utils.unregister_class(KsynSolidColorCustomIconPanel)
    bpy.utils.unregister_class(KsynSolidColorOBJECT_OT_RefreshIcons)

if __name__ == "__main__":
    register()