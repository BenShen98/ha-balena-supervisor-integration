import { LitElement, html, css, nothing } from "https://cdn.jsdelivr.net/npm/lit@3.3.1/+esm";

class MoreInfoBalendDocker extends LitElement {

  static get properties() {
    return { hass: {}, stateObj: {} };
  }


  render() {
    if (!this.stateObj) return html``;

    return html`
        <div style="padding: 16px;">
          <ha-button @click=${() => this._callWs("start-service")}>Start</ha-button>
          <ha-button @click=${() => this._callWs("stop-service")}>Stop</ha-button>
          <ha-button @click=${() => this._callWs("restart-service")}>Restart</ha-button>
        </div>
    `;
  }

  async _callWs(action) {
    await this.hass.connection.sendMessagePromise({
      type: "balena_docker/control_container",
      entity_id: this.stateObj.entity_id,
      action,
    });
  }

  getCardSize() {
    return 2;
  }
}

customElements.define("more-info-balena_docker", MoreInfoBalendDocker);