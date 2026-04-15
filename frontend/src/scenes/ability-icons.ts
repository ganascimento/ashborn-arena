import broadsword from "@iconify-icons/game-icons/broadsword";
import fireIcon from "@iconify-icons/game-icons/fire";
import snowflake from "@iconify-icons/game-icons/snowflake-2";
import lightningHelix from "@iconify-icons/game-icons/lightning-helix";
import poisonBottle from "@iconify-icons/game-icons/poison-bottle";
import healingIcon from "@iconify-icons/game-icons/health-potion";
import wizardStaff from "@iconify-icons/game-icons/wizard-staff";
import questionMark from "@iconify-icons/game-icons/uncertainty";

interface IconData {
  width?: number;
  height?: number;
  body: string;
}

const ICON_MAP: Record<string, IconData> = {
  physical: broadsword,
  magical: wizardStaff,
  heal: healingIcon,
  fire: fireIcon,
  ice: snowflake,
  electric: lightningHelix,
  poison: poisonBottle,
  unknown: questionMark,
};

function iconToDataUrl(icon: IconData, fill: string): string {
  const w = icon.width ?? 512;
  const h = icon.height ?? 512;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" fill="${fill}">${icon.body}</svg>`;
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}

export function loadAbilityIcons(scene: Phaser.Scene): Promise<void> {
  const promises: Promise<void>[] = [];

  for (const [key, icon] of Object.entries(ICON_MAP)) {
    const texKey = `ability_icon_${key}`;
    if (scene.textures.exists(texKey)) continue;

    const dataUrl = iconToDataUrl(icon, "#ffffff");
    promises.push(
      new Promise<void>((resolve) => {
        const img = new Image();
        img.onload = () => {
          if (!scene.textures.exists(texKey)) {
            scene.textures.addImage(texKey, img);
          }
          resolve();
        };
        img.onerror = () => resolve();
        img.src = dataUrl;
      }),
    );
  }

  return Promise.all(promises).then(() => {});
}

export function getIconTextureKey(abilityType: string): string {
  if (abilityType in ICON_MAP) return `ability_icon_${abilityType}`;
  return "ability_icon_unknown";
}
