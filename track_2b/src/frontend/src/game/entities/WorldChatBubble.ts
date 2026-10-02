import * as Phaser from "phaser";

const PANEL_WIDTH = 260;
const PANEL_PADDING_X = 10;
const PANEL_PADDING_Y = 8;
const PANEL_RADIUS = 8;
const TAIL_HEIGHT = 10;
const STEM_HEIGHT = 12;
const NAME_GAP = 6;
const MESSAGE_GAP = 4;
const MAX_MESSAGE_LENGTH = 80;

const PANEL_BG = 0xfdf5e6;
const PANEL_BORDER = 0xa0824a;
const STEM_COLOR = 0xc4a46c;
const NAME_COLOR = "#5B3A1E";
const CATEGORY_COLOR = "#A0824A";
const MESSAGE_COLOR = "#6B4C2A";
const EVENT_LOG_FONT_FAMILY = 'ui-monospace, "Courier New", monospace';

export class WorldChatBubble extends Phaser.GameObjects.Container {
  private panel = this.scene.add.graphics();
  private outerTail = this.scene.add.triangle(
    0,
    0,
    -8,
    0,
    8,
    0,
    0,
    TAIL_HEIGHT,
    PANEL_BORDER,
  );
  private innerTail = this.scene.add.triangle(
    0,
    0,
    -6,
    0,
    6,
    0,
    0,
    TAIL_HEIGHT - 2,
    PANEL_BG,
  );
  private stem = this.scene.add.rectangle(0, 0, 2, STEM_HEIGHT, STEM_COLOR);
  private nameText = this.scene.add.text(0, 0, "", {
    fontFamily: EVENT_LOG_FONT_FAMILY,
    fontSize: "14px",
    fontStyle: "bold",
    color: NAME_COLOR,
  });
  private categoryText = this.scene.add.text(0, 0, "", {
    fontFamily: EVENT_LOG_FONT_FAMILY,
    fontSize: "11px",
    color: CATEGORY_COLOR,
  });
  private messageText = this.scene.add.text(0, 0, "", {
    fontFamily: EVENT_LOG_FONT_FAMILY,
    fontSize: "12px",
    color: MESSAGE_COLOR,
    wordWrap: {
      width: PANEL_WIDTH - PANEL_PADDING_X * 2,
      useAdvancedWrap: true,
    },
  });

  constructor(
    scene: Phaser.Scene,
    agentName: string,
    message: string,
    agentCategory?: string,
  ) {
    super(scene, 0, 0);
    this.setDepth(30);
    this.add([
      this.panel,
      this.outerTail,
      this.innerTail,
      this.stem,
      this.nameText,
      this.categoryText,
      this.messageText,
    ]);
    scene.add.existing(this);
    this.updateContent(agentName, message, agentCategory);
  }

  updateContent(agentName: string, message: string, agentCategory?: string) {
    const displayMessage =
      message.length > MAX_MESSAGE_LENGTH
        ? `${message.slice(0, MAX_MESSAGE_LENGTH)}...`
        : message;

    this.nameText.setText(agentName);
    this.categoryText.setText(agentCategory ?? "");
    this.categoryText.setVisible(!!agentCategory);
    this.messageText.setText(displayMessage);

    const headerY = 0;
    this.nameText.setPosition(-PANEL_WIDTH / 2 + PANEL_PADDING_X, headerY);

    let headerHeight = this.nameText.height;
    if (agentCategory) {
      this.categoryText.setPosition(
        this.nameText.x + this.nameText.width + NAME_GAP,
        headerY + 2,
      );
      headerHeight = Math.max(headerHeight, this.categoryText.height + 2);
    }

    const messageY = headerY + headerHeight + MESSAGE_GAP;
    this.messageText.setPosition(-PANEL_WIDTH / 2 + PANEL_PADDING_X, messageY);

    const panelHeight =
      PANEL_PADDING_Y * 2 +
      headerHeight +
      MESSAGE_GAP +
      this.messageText.height;
    const panelTop = -(panelHeight + TAIL_HEIGHT + STEM_HEIGHT);
    const panelBottom = panelTop + panelHeight;

    this.panel.clear();
    this.panel.fillStyle(PANEL_BG, 1);
    this.panel.lineStyle(2, PANEL_BORDER, 1);
    this.panel.fillRoundedRect(
      -PANEL_WIDTH / 2,
      panelTop,
      PANEL_WIDTH,
      panelHeight,
      PANEL_RADIUS,
    );
    this.panel.strokeRoundedRect(
      -PANEL_WIDTH / 2,
      panelTop,
      PANEL_WIDTH,
      panelHeight,
      PANEL_RADIUS,
    );

    this.nameText.y = panelTop + PANEL_PADDING_Y;
    if (agentCategory) {
      this.categoryText.y = panelTop + PANEL_PADDING_Y + 2;
    }
    this.messageText.y =
      panelTop + PANEL_PADDING_Y + headerHeight + MESSAGE_GAP;

    this.outerTail.setPosition(0, panelBottom);
    this.innerTail.setPosition(0, panelBottom + 1);
    this.stem.setPosition(0, -(STEM_HEIGHT / 2));
  }

  updateAnchor(x: number, y: number) {
    this.setPosition(Math.round(x), Math.round(y));
  }
}
