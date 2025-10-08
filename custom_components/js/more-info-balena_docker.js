import { LitElement, html, css, nothing } from "https://cdn.jsdelivr.net/npm/lit@3.3.1/+esm";

// Listen for when more-info-content is defined
customElements.whenDefined("more-info-content").then(() => {
  console.log("more-info-content is defined, applying override");

  // Get the original element constructor
  const OriginalMoreInfoContent = customElements.get("more-info-content");

  // Save the original render method
  const originalRender = OriginalMoreInfoContent.prototype.render;

  // Override the render method to append our custom component
  OriginalMoreInfoContent.prototype.render = function() {
    // Get the original rendered content
    const originalResult = originalRender.call(this);

    // Only append for balena_docker entities
    debugger;
    if (this.stateObj && this.hass && this.hass.entities[this.stateObj.entity_id]?.platform == "balena_docker") {
      console.log("Adding balena_docker controls for:", this.stateObj.entity_id);

      // Create a wrapper to contain both original content and our custom content
      return html`
        ${originalResult}
        <more-info-balena_docker
          .hass=${this.hass}
          .stateObj=${this.stateObj}
        ></more-info-balena_docker>
      `;
    }

    // For other entities, return original content unchanged
    return originalResult;
  };

  console.log("Successfully overrode more-info-content render method");
});

class MoreInfoBalenaDocker extends LitElement {
  static get properties() {
    return {
      hass: { attribute: false },
      stateObj: { attribute: false },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        padding: 8px 0;
        border-top: 1px solid var(--divider-color);
        margin-top: 12px;
      }
      .controls {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 16px;
      }
      ha-button[disabled] {
        opacity: 0.5;
        cursor: not-allowed;
      }
    `;
  }

  render() {
    if (!this.stateObj) return html``;

    const isRunning = this.stateObj.state === "running";

    return html`
      <div class="controls">
        <ha-button
          @click=${() => this._callWs("start-service")}
          .disabled=${isRunning}
        >Start</ha-button>

        <ha-button
          @click=${() => this._callWs("stop-service")}
          .disabled=${!isRunning}
        >Stop</ha-button>

        <ha-button
          @click=${() => this._callWs("restart-service")}
          .disabled=${!isRunning}
        >Restart</ha-button>
      </div>
    `;
  }

  async _callWs(action) {
    try {
      console.log(`Sending ${action} for ${this.stateObj.entity_id}`);

      await this.hass.connection.sendMessagePromise({
        type: "balena_docker/control_container",
        entity_id: this.stateObj.entity_id,
        action,
      });

      // Optionally refresh entity state after action
      this.hass.callService("homeassistant", "update_entity", {
        entity_id: this.stateObj.entity_id,
      });
    } catch (err) {
      console.error(`Error in ${action}:`, err);
    }
  }
}

customElements.define("more-info-balena_docker", MoreInfoBalenaDocker);