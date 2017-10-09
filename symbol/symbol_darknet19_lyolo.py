"""
Reference:
Redmon, Joseph, and Ali Farhadi. "YOLO9000: Better, Faster, Stronger."
"https://arxiv.org/pdf/1612.08242.pdf"
"""
import mxnet as mx
from symbol_darknet19 import get_symbol as get_darknet19
from symbol_darknet19 import conv_act_layer

def get_symbol(num_classes=20, nms_thresh=0.5, force_nms=False, **kwargs):
    bone = get_darknet19(num_classes=num_classes, **kwargs)
    conv3_3 = bone.get_internals()["conv3_3_output"]
    conv4_3 = bone.get_internals()["conv4_3_output"]
    conv5_5 = bone.get_internals()["conv5_5_output"]
    conv6_5 = bone.get_internals()["conv6_5_output"]
    # anchors
    anchors = [0.4, 0.4,
               1.3221, 1.73145,
               3.19275, 4.00944,
               5.05587, 8.09892,
               9.47112, 4.84053,
               11.2364, 10.0071]
    num_anchor = len(anchors) // 2

    # extra layers
    conv7_1 = conv_act_layer(conv6_5, 'conv7_1', 1024, kernel=(3, 3), pad=(1, 1),
        act_type='leaky')
    conv7_2 = conv_act_layer(conv7_1, 'conv7_2', 1024, kernel=(3, 3), pad=(1, 1),
        act_type='leaky')

    # re-organze conv5_5 and concat conv7_2
    conv3_4 = mx.sym.stack_neighbor(data=conv3_3, kernel=(8, 8))
    conv4_4 = mx.sym.stack_neighbor(data=conv4_3, kernel=(4, 4))
    conv5_6 = mx.sym.stack_neighbor(data=conv5_5, kernel=(2, 2))
    concat = mx.sym.Concat(*[conv3_4, conv4_4, conv5_6, conv7_2], dim=1)
    # concat = conv7_2
    conv8_1 = conv_act_layer(concat, 'conv8_1', 1024, kernel=(3, 3), pad=(1, 1),
        act_type='leaky')
    pred = mx.symbol.Convolution(data=conv8_1, name='conv_pred', kernel=(1, 1),
        num_filter=num_anchor * (num_classes + 4 + 1))

    out = mx.contrib.symbol.YoloOutput(data=pred, num_class=num_classes,
        num_anchor=num_anchor, object_grad_scale=5.0, background_grad_scale=1.0,
        coord_grad_scale=1.0, class_grad_scale=1.0, anchors=anchors,
        nms_topk=400, warmup_samples=12800, name='yolo_output')
    return out
