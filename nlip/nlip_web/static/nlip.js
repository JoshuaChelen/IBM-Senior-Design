function nlipCompareString(value1, value2, matchNone = false) {
  if (value1 != null && value2 != null) {
    return value1.toLowerCase() === value2.toLowerCase();
  }
  if (matchNone) {
    return true;
  } else {
    return value1 == null && value2 == null;
  }
}

const AllowedFormats = {
  text: "text",
  token: "token",
  structured: "structured",
  binary: "binary",
  location: "location",
  error: "error",
  generic: "generic"
};

// Usage example:
// const format = CaseInsensitiveEnum.fromValue(AllowedFormats, "ToKeN"); // returns "token"

class CaseInsensitiveEnum {
  constructor(enumObj) {
    this.enumObj = enumObj;
    this.values = Object.values(enumObj);
  }

  static fromValue(enumObj, value) {
    if (typeof value !== 'string') return null;
    const lowerValue = value.toLowerCase();
    for (const key in enumObj) {
      if (enumObj[key].toLowerCase() === lowerValue) {
        return enumObj[key];
      }
    }
    return null;
  }
}

const ReservedTokens = {
  auth: 'authorization',
  conv: 'conversation',
  control: 'control',

  isReserved(field) {
    if (typeof field !== 'string') return false;
    const lower = field.toLowerCase();
    return lower.startsWith(this.auth) || lower.startsWith(this.conv);
  },

  isAuth(field) {
    return typeof field === 'string' && field.toLowerCase().startsWith(this.auth);
  },

  isConv(field) {
    return typeof field === 'string' && field.toLowerCase().startsWith(this.conv);
  },

  isControl(field) {
    return nlipCompareString(this.control, field);
  },

  getSuffix(field, separator = '') {
    if (this.isAuth(field)) {
      return field.slice(this.auth.length + separator.length).trim();
    } else if (this.isConv(field)) {
      return field.slice(this.conv.length + separator.length).trim();
    } else {
      return field;
    }
  }
};

class NLIPSubMessage {
  /**
   * @param {string} format - One of the AllowedFormats
   * @param {string} subformat
   * @param {string|Object} content
   * @param {string|null} label
   */
  constructor(format, subformat, content, label = null) {
    this.format = format;
    this.subformat = subformat;
    this.content = content;
    this.label = label;
  }

  updateContent(content) {
    this.content = content;
  }

  extractField(format, subformat = null, label = null) {
    if (nlipCompareString(this.format, format)) {
      if (nlipCompareString(this.subformat, subformat, true)) {
        if (nlipCompareString(this.label, label, true)) {
          return this.content;
        }
      }
    }
    return null;
  }
}


class NLIPMessage {
  constructor({ messagetype = null, format, subformat, content, label = null, submessages = [] }) {
    this.messagetype = messagetype;
    this.format = format;
    this.subformat = subformat;
    this.content = content;
    this.label = label;
    this.submessages = submessages;
  }

  isControlMsg() {
    return this.messagetype !== null && ReservedTokens.isControl(this.messagetype);
  }

  addSubmessage(submsg) {
    if (!Array.isArray(this.submessages)) {
      this.submessages = [];
    }
    this.submessages.push(submsg);
  }

  addConversationToken(conversationToken, forceChange = false, label = null) {
    const existingToken = this.extractConversationToken(label);
    const submsg = new NLIPSubMessage(AllowedFormats.token, ReservedTokens.conv, conversationToken, label);

    if (existingToken === null) {
      this.addSubmessage(submsg);
    } else if (forceChange) {
      this.submessages.forEach((msg, i) => {
        if (ReservedTokens.isConv(msg.subformat)) {
          this.submessages[i].updateContent(conversationToken);
        }
      });
    }
  }

  addAuthenticationToken(token, label = null) {
    const existingToken = this.extractAuthenticationToken(label);
    if (existingToken === null) {
      this.addSubmessage(new NLIPSubMessage(AllowedFormats.token, ReservedTokens.auth, token, label));
    }
  }

  extractField(format, subformat = null, label = null) {
    if (
      nlipCompareString(this.format, format) &&
      nlipCompareString(this.subformat, subformat, true) &&
      nlipCompareString(this.label, label, true)
    ) {
      return this.content;
    }
    return null;
  }

  extractFieldList(format, subformat = null, label = null) {
    const field = this.extractField(format, subformat, label);
    let fieldList = field === null ? [] : [field];

    if (Array.isArray(this.submessages)) {
      this.submessages.forEach(submsg => {
        const value = submsg.extractField(format, subformat, label);
        if (value !== null) {
          fieldList.push(value);
        }
      });
    }

    return fieldList;
  }

  extractText(language = 'english', separator = ' ') {
    const textList = this.extractFieldList(AllowedFormats.text, language);
    return textList.length > 0 ? textList.join(separator) : null;
  }

  findLabeledSubmessage(label) {
    if (label === null) return null;
    return this.submessages.find(submsg => nlipCompareString(submsg.label, label)) || null;
  }

  extractToken(tokenType, label = null) {
    const tokens = this.extractFieldList(AllowedFormats.token, tokenType, label);
    return tokens.length > 0 ? tokens[0] : null;
  }

  extractConversationToken(label = null) {
    return this.extractToken(ReservedTokens.conv, label);
  }

  extractAuthenticationToken(label = null) {
    return this.extractToken(ReservedTokens.auth, label);
  }

  toJSON() {
    const obj = {
      messagetype: this.messagetype,
      format: this.format,
      subformat: this.subformat,
      content: this.content,
      label: this.label,
      submessages: this.submessages.length > 0 ? this.submessages : undefined
    };
    return JSON.stringify(obj, (_, v) => (v === null ? undefined : v));
  }

  toDict() {
    return JSON.parse(this.toJSON());
  }

  addText(content, language = 'english', label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.text, language, content, label));
  }

  addToken(token, tokenType, label = null) {
    if (ReservedTokens.isAuth(tokenType)) {
      return this.addAuthenticationToken(token, label);
    }
    if (ReservedTokens.isConv(tokenType)) {
      return this.addConversationToken(token, true, label);
    }
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.token, tokenType, token, label));
  }

  addJson(jsonDict, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.structured, "JSON", jsonDict, label));
  }

  addStructuredText(content, contentType, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.structured, contentType, content, label));
  }

  addBinary(content, binaryType, encoding, label = null) {
    const subformat = `${binaryType}/${encoding}`;
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.binary, subformat, content, label));
  }

  addImage(content, encoding, label = null) {
    this.addBinary(content, "image", encoding, label);
  }

  addAudio(content, encoding, label = null) {
    this.addBinary(content, "audio", encoding, label);
  }

  addVideo(content, encoding, label = null) {
    this.addBinary(content, "video", encoding, label);
  }

  addLocationText(location, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.location, "text", location, label));
  }

  addLocationGps(location, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.location, "gps", location, label));
  }

  addErrorCode(errorCode, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.error, "code", errorCode, label));
  }

  addErrorText(errorDescr, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.error, "text", errorDescr, label));
  }

  addGeneric(content, subformat, label = null) {
    this.addSubmessage(new NLIPSubMessage(AllowedFormats.generic, subformat, content, label));
  }
}


class NLIPFactory {
  static createText(content, language = 'english', messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.text, subformat: language, content, label });
  }

  static createControl(content, language = 'english', label = null) {
    return new NLIPMessage({ messagetype: ReservedTokens.control, format: AllowedFormats.text, subformat: language, content, label });
  }

  static createToken(token, tokenType, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.token, subformat: tokenType, content: token, label });
  }

  static createJson(jsonDict, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.structured, subformat: "JSON", content: jsonDict, label });
  }

  static createStructured(content, contentType, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.structured, subformat: contentType, content, label });
  }

  static createBinary(content, binaryType, encoding, messagetype = null, label = null) {
    const subformat = `${binaryType}/${encoding}`;
    return new NLIPMessage({ messagetype, format: AllowedFormats.binary, subformat, content, label });
  }

  static createImage(content, encoding, messagetype = null, label = null) {
    return this.createBinary(content, "image", encoding, messagetype, label);
  }

  static createAudio(content, encoding, messagetype = null, label = null) {
    return this.createBinary(content, "audio", encoding, messagetype, label);
  }

  static createVideo(content, encoding, messagetype = null, label = null) {
    return this.createBinary(content, "video", encoding, messagetype, label);
  }

  static createLocationText(location, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.location, subformat: "text", content: location, label });
  }

  static createLocationGps(location, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.location, subformat: "gps", content: location, label });
  }

  static createErrorCode(errorCode, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.error, subformat: "code", content: errorCode, label });
  }

  static createErrorText(errorDescr, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.error, subformat: "text", content: errorDescr, label });
  }

  static createGeneric(content, subformat, messagetype = null, label = null) {
    return new NLIPMessage({ messagetype, format: AllowedFormats.generic, subformat, content, label });
  }

  static createSubMessageFromJSON(jsonObject) {
    return new NLIPSubMessage(jsonObject.format, jsonObject.subformat, jsonObject.content, jsonObject.label)
  }

  static createMessageFromJSON(jsonObject) {
    let submessages = null
    if (jsonObject.submessages != null) {
      submessages = jsonObject.submessages.map(sm => new NLIPSubMessage(sm.format, sm.subformat, sm.content, sm.label))
    } 

    return new NLIPMessage({messagetype: jsonObject.messagetype, 
      format: jsonObject.format, subformat: jsonObject.subformat, content: jsonObject.content,
      label: jsonObject.label, submessages: submessages})
  }
}

class NLIPClient {
  constructor(baseUrl = '', options = {}) {
    this.baseUrl = baseUrl;
    this.options = { timeout: 30000, ...options };
    this.correlator = null
  }

  async sendMessage(text) {
    const message = NLIPFactory.createText(text);
    if (this.correlator != null) {
      message.addConversationToken(this.correlator)
    }
    const response = await this.send(message);
    const nlipMessage = NLIPFactory.createMessageFromJSON(response)
    this.correlator = nlipMessage.extractToken(ReservedTokens.conv)
    
    const extractedText = nlipMessage.extractText()
    return extractedText
  }

  async sendWithImage(text, imageFile) {
    const base64 = await this.fileToBase64(imageFile);
    const message = NLIPFactory.createText(text);
    message.addImage(base64, this.getFileExtension(imageFile));
    return this.send(message);
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('contents', file);
    
    const response = await fetch(`${this.baseUrl}/nlip/upload/`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }

  async send(nlipMessage) {
    const response = await fetch(`${this.baseUrl}/nlip/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: nlipMessage.toJSON(),
      signal: AbortSignal.timeout(this.options.timeout)
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // Utility methods
  async fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  getFileExtension(file) {
    return file.name.split('.').pop() || 'bin';
  }
}

export { NLIPMessage, NLIPFactory, NLIPClient, AllowedFormats, ReservedTokens, nlipCompareString, CaseInsensitiveEnum };
