import qs.services
import qs.modules.common
import qs.modules.common.functions
import Qt5Compat.GraphicalEffects
import QtQuick
import Quickshell
import Quickshell.Widgets
import Quickshell.Services.Notifications

MaterialShape { // App icon
    id: root
    property var appIcon: ""
    property var summary: ""
    property var urgency: NotificationUrgency.Normal
    property bool isUrgent: urgency === NotificationUrgency.Critical
    property var image: ""
    property real materialIconScale: 0.57
    property real appIconScale: 0.8
    property real smallAppIconScale: 0.49
    property real materialIconSize: implicitSize * materialIconScale
    property real appIconSize: implicitSize * appIconScale
    property real smallAppIconSize: implicitSize * smallAppIconScale
    property bool imageFailed: false
    property bool appIconFailed: false
    readonly property bool showImage: image != "" && !imageFailed
    // iconPath() with a fallback draws Qt's magenta/black "missing" texture as a successful load, so paths load directly and names are checked
    readonly property string appIconSource: Notifications.localPath(appIcon).startsWith("/") ? `file://${Notifications.localPath(appIcon)}` : Quickshell.iconPath(appIcon, true)
    readonly property string imageSource: Notifications.localPath(image).startsWith("/") ? `file://${Notifications.localPath(image)}` : image
    readonly property bool showAppIcon: appIconSource != "" && !appIconFailed
    onImageChanged: imageFailed = false
    onAppIconChanged: appIconFailed = false

    implicitSize: 38 * scale
    property list<var> urgentShapes: [
        MaterialShape.Shape.VerySunny,
        MaterialShape.Shape.SoftBurst,
    ]
    shape: isUrgent ? urgentShapes[Math.floor(Math.random() * urgentShapes.length)] : MaterialShape.Shape.Circle

    color: isUrgent ? Appearance.colors.colPrimaryContainer : Appearance.colors.colSecondaryContainer
    Loader {
        id: materialSymbolLoader
        active: !root.showImage && !root.showAppIcon
        anchors.fill: parent
        sourceComponent: MaterialSymbol {
            text: {
                const defaultIcon = NotificationUtils.findSuitableMaterialSymbol("")
                const guessedIcon = NotificationUtils.findSuitableMaterialSymbol(root.summary)
                return (root.urgency == NotificationUrgency.Critical && guessedIcon === defaultIcon) ?
                    "priority_high" : guessedIcon
            }
            anchors.fill: parent
            color: isUrgent ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnSecondaryContainer
            iconSize: root.materialIconSize
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
    Loader {
        id: appIconLoader
        active: !root.showImage && root.showAppIcon
        anchors.centerIn: parent
        sourceComponent: IconImage {
            id: appIconImage
            implicitSize: root.appIconSize
            asynchronous: true
            source: root.appIconSource
            onStatusChanged: if (status === Image.Error) root.appIconFailed = true
        }
    }
    Loader {
        id: notifImageLoader
        active: root.showImage
        anchors.fill: parent
        sourceComponent: Item {
            anchors.fill: parent
            StyledImage {
                id: notifImage
                anchors.fill: parent
                readonly property int size: parent.width

                source: root.imageSource
                fillMode: Image.PreserveAspectCrop
                cache: false
                antialiasing: true
                asynchronous: true
                onStatusChanged: {
                    if (status === Image.Error) {
                        root.imageFailed = true;
                    } else if (status === Image.Ready && root.image.startsWith("image://qsimage/")) {
                        const url = root.image;
                        grabToImage(result => Notifications.storeGrabbedImage(url, result), sourceSize);
                    }
                }

                layer.enabled: true
                layer.effect: OpacityMask {
                    maskSource: Rectangle {
                        width: notifImage.size
                        height: notifImage.size
                        radius: Appearance.rounding.full
                    }
                }
            }
            Loader {
                id: notifImageAppIconLoader
                active: root.showAppIcon
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                sourceComponent: IconImage {
                    implicitSize: root.smallAppIconSize
                    asynchronous: true
                    source: root.appIconSource
                    onStatusChanged: if (status === Image.Error) root.appIconFailed = true
                }
            }
        }
    }
}